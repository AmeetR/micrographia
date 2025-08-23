from pathlib import Path
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
import torch
import pandas as pd
import yaml
import importlib


def bitsandbytes_ok():
    try:
        import bitsandbytes  # noqa: F401
        return True
    except Exception:
        return False


def format_for_sft(tok, max_len):
    def _fmt(batch):
        texts = []
        for ex in batch:
            prompt = ex.get("input.prompt") or ex.get("input", {}).get("prompt")
            target = ex.get("target.json") or ex.get("target.text") or ex.get("target", {}).get("json")
            if isinstance(target, dict):
                target = importlib.import_module("orjson").dumps(target).decode()
            text = prompt.strip() + "\n" + str(target).strip() + tok.eos_token
            texts.append(text[:max_len])
        return {"text": texts}

    return _fmt


def run(cfg_path: Path, exp: str):
    cfg = yaml.safe_load(Path(cfg_path).read_text())
    base_id = cfg["base_id"]
    outdir = Path(cfg["system"]["output_dir"].format(exp=exp))
    outdir.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(base_id, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_id,
        device_map="auto",
        load_in_4bit=cfg["quant"]["load_in_4bit"] and bitsandbytes_ok(),
        torch_dtype=torch.bfloat16 if cfg["system"]["bf16"] else torch.float16,
    )
    model.enable_input_require_grads()

    lcfg = LoraConfig(
        r=cfg["peft"]["r"],
        lora_alpha=cfg["peft"]["alpha"],
        lora_dropout=cfg["peft"]["dropout"],
        target_modules=cfg["peft"]["target_modules"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lcfg)

    train_df = pd.read_parquet(cfg["data"]["train_path"].replace("{exp}", exp))
    eval_df = pd.read_parquet(cfg["data"]["eval_path"].replace("{exp}", exp))
    train_ds = Dataset.from_pandas(train_df)
    eval_ds = Dataset.from_pandas(eval_df)
    train_ds = train_ds.map(format_for_sft(tok, cfg["train"]["max_seq_len"]), batched=False)
    eval_ds = eval_ds.map(format_for_sft(tok, cfg["train"]["max_seq_len"]), batched=False)

    args = TrainingArguments(
        output_dir=str(outdir),
        per_device_train_batch_size=cfg["train"]["per_device_train_batch_size"],
        gradient_accumulation_steps=cfg["train"]["gradient_accumulation_steps"],
        learning_rate=cfg["train"]["lr"],
        num_train_epochs=cfg["train"]["epochs"],
        warmup_ratio=cfg["train"]["warmup_ratio"],
        bf16=cfg["system"]["bf16"],
        logging_steps=25,
        evaluation_strategy="steps",
        eval_steps=200,
        save_steps=500,
        gradient_checkpointing=cfg["system"]["gradient_checkpointing"],
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tok,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        args=args,
        dataset_text_field="text",
        packing=cfg["train"]["packing"],
    )
    trainer.train()
    adapter_dir = outdir / "adapter"
    adapter_dir.mkdir(exist_ok=True, parents=True)
    model.save_pretrained(adapter_dir)
    tok.save_pretrained(adapter_dir)
    (outdir / "train_report.json").write_text("{\"ok\":true}")
    return adapter_dir
