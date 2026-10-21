#!/usr/bin/env python3
"""Convert a merged Hugging Face checkpoint to a Q4_K_M GGUF for Ollama."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


SYSTEM = """You are StudyBuddy Advanced, a careful local student and coding assistant. Give complete runnable code when requested, explain how to run it, handle edge cases, check arithmetic and assumptions, and distinguish verified facts from uncertainty. Never claim to be Astra or to have tools that are not available. Use clear, structured answers and teach concepts in simple language."""


def run(command: list[str], cwd: Path | None = None) -> None:
    print("\n$", " ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged-model", type=Path, required=True,
                        help="Directory created by train_lora.py, e.g. merged-fp16.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--llama-cpp-dir", type=Path, default=Path("/content/llama.cpp"))
    args = parser.parse_args()

    merged = args.merged_model.resolve()
    output = args.output_dir.resolve()
    llama = args.llama_cpp_dir.resolve()
    if not (merged / "config.json").is_file():
        raise SystemExit(f"No config.json found in merged model directory: {merged}")
    if not (merged / "model.safetensors").exists() and not list(merged.glob("model-*.safetensors")):
        raise SystemExit(f"No Safetensors model weights found in: {merged}")
    output.mkdir(parents=True, exist_ok=True)

    if not (llama / "convert_hf_to_gguf.py").is_file():
        if llama.exists() and any(llama.iterdir()):
            raise SystemExit(f"{llama} exists but does not look like a llama.cpp checkout. Pass --llama-cpp-dir or remove that folder.")
        run(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(llama)])
    quantizer = llama / "build" / "bin" / "llama-quantize"
    if not quantizer.is_file():
        run(["cmake", "-S", str(llama), "-B", str(llama / "build"),
             "-DCMAKE_BUILD_TYPE=Release", "-DLLAMA_CURL=OFF", "-DGGML_CUDA=OFF"])
        run(["cmake", "--build", str(llama / "build"), "--config", "Release", "-j2", "--target", "llama-quantize"])
    if not quantizer.is_file():
        raise SystemExit(f"llama-quantize was not built at {quantizer}")

    f16_gguf = output / "studybuddy-advanced-trained-f16.gguf"
    q4_gguf = output / "studybuddy-advanced-trained-q4_k_m.gguf"
    run([sys.executable, str(llama / "convert_hf_to_gguf.py"), str(merged),
         "--outfile", str(f16_gguf), "--outtype", "f16"])
    run([str(quantizer), str(f16_gguf), str(q4_gguf), "Q4_K_M"])

    modelfile = output / "Modelfile.trained"
    modelfile.write_text(
        "FROM ./studybuddy-advanced-trained-q4_k_m.gguf\n"
        "PARAMETER temperature 0.25\n"
        "PARAMETER top_p 0.8\n"
        "PARAMETER repeat_penalty 1.1\n"
        "PARAMETER num_ctx 2048\n"
        'SYSTEM """\n' + SYSTEM + '\n"""\n',
        encoding="utf-8",
    )
    package = output / "studybuddy-advanced-import.zip"
    with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(q4_gguf, arcname=q4_gguf.name)
        archive.write(modelfile, arcname=modelfile.name)
    print("\nSUCCESS")
    print(f"GGUF model: {q4_gguf}")
    print(f"Ollama Modelfile: {modelfile}")
    print(f"Windows import package: {package}")
    print("The ZIP contains the GGUF and Modelfile together. Copy it to Windows, extract it, then run:")
    print("ollama create studybuddy-advanced-trained -f Modelfile.trained")


if __name__ == "__main__":
    main()
