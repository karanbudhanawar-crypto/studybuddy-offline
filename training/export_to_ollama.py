#!/usr/bin/env python3
"""Convert a merged Hugging Face checkpoint to a Q4_K_M GGUF for Ollama."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile


SYSTEM = """You are StudyBuddy Advanced, a careful local student and coding assistant. Give complete runnable code when requested, explain how to run it, handle edge cases, check arithmetic and assumptions, and distinguish verified facts from uncertainty. Never claim to be Astra or to have tools that are not available. Use clear, structured answers and teach concepts in simple language."""


def run(command: list[str], cwd: Path | None = None) -> None:
    print("\n$", " ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def find_quantizer(build_dir: Path) -> Path | None:
    candidates = [
        build_dir / "bin" / "llama-quantize",
        build_dir / "bin" / "llama-quantize.exe",
        build_dir / "bin" / "Release" / "llama-quantize.exe",
        build_dir / "bin" / "Debug" / "llama-quantize.exe",
        build_dir / "bin" / "RelWithDebInfo" / "llama-quantize.exe",
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged-model", type=Path, required=True,
                        help="Directory created by train_cpu_lora.py or train_lora.py.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--llama-cpp-dir", type=Path, default=Path("tools/llama.cpp"))
    parser.add_argument("--model-name", default="studybuddy-advanced-trained",
                        help="Name to pass to ollama create, for example studybuddy-cpu-trained.")
    parser.add_argument("--jobs", type=int, default=2, help="CMake build jobs; use 1 or 2 on low-RAM PCs.")
    args = parser.parse_args()

    if args.jobs < 1 or args.jobs > 4:
        raise SystemExit("--jobs must be between 1 and 4 on this low-resource workflow.")
    name = re.sub(r"[^a-zA-Z0-9_-]+", "-", args.model_name).strip("-").lower()
    if not name:
        raise SystemExit("--model-name must contain letters or numbers.")

    merged = args.merged_model.resolve()
    output = args.output_dir.resolve()
    llama = args.llama_cpp_dir.resolve()
    if not (merged / "config.json").is_file():
        raise SystemExit(f"No config.json found in merged model directory: {merged}")
    if not (merged / "model.safetensors").exists() and not list(merged.glob("model-*.safetensors")):
        raise SystemExit(f"No Safetensors model weights found in: {merged}")
    if not shutil.which("git"):
        raise SystemExit("Git is required to download llama.cpp. Install Git for Windows and restart Command Prompt.")
    if not shutil.which("cmake"):
        raise SystemExit("CMake is required to build the CPU quantizer. Install CMake and Visual Studio Build Tools 2022 with 'Desktop development with C++'.")
    output.mkdir(parents=True, exist_ok=True)

    if not (llama / "convert_hf_to_gguf.py").is_file():
        if llama.exists() and any(llama.iterdir()):
            raise SystemExit(f"{llama} exists but does not look like a llama.cpp checkout. Pass --llama-cpp-dir or rename/remove that folder.")
        run(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(llama)])

    # convert_hf_to_gguf.py imports the gguf Python package.
    run([sys.executable, "-m", "pip", "install", "--upgrade", "gguf"])
    build_dir = llama / "build"
    quantizer = find_quantizer(build_dir)
    if quantizer is None:
        print(
            "\nBuilding the CPU-only quantizer. On Windows this requires a working C++ compiler "
            "(Visual Studio Build Tools, 'Desktop development with C++'). The first build can take time.",
            flush=True,
        )
        run([
            "cmake", "-S", str(llama), "-B", str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release", "-DLLAMA_CURL=OFF", "-DGGML_CUDA=OFF",
        ])
        run([
            "cmake", "--build", str(build_dir), "--config", "Release",
            f"-j{args.jobs}", "--target", "llama-quantize",
        ])
        quantizer = find_quantizer(build_dir)
    if quantizer is None:
        raise SystemExit(
            "llama-quantize was not built. Check the CMake output above. On Windows install "
            "Visual Studio Build Tools 2022 and its 'Desktop development with C++' workload."
        )

    f16_gguf = output / f"{name}-f16.gguf"
    q4_gguf = output / f"{name}-q4_k_m.gguf"
    run([
        sys.executable, str(llama / "convert_hf_to_gguf.py"), str(merged),
        "--outfile", str(f16_gguf), "--outtype", "f16",
    ])
    run([str(quantizer), str(f16_gguf), str(q4_gguf), "Q4_K_M"])

    modelfile = output / "Modelfile.trained"
    modelfile.write_text(
        f"FROM ./{q4_gguf.name}\n"
        "PARAMETER temperature 0.25\n"
        "PARAMETER top_p 0.8\n"
        "PARAMETER repeat_penalty 1.1\n"
        "PARAMETER num_ctx 2048\n"
        'SYSTEM """\n' + SYSTEM + '\n"""\n',
        encoding="utf-8",
    )
    package = output / f"{name}-import.zip"
    # GGUF is already compressed/quantized; store it directly to avoid CPU-heavy zip compression.
    with ZipFile(package, "w", compression=ZIP_STORED) as archive:
        archive.write(q4_gguf, arcname=q4_gguf.name)
        archive.write(modelfile, arcname=modelfile.name)
    print("\nSUCCESS")
    print(f"GGUF model: {q4_gguf}")
    print(f"Ollama Modelfile: {modelfile}")
    print(f"Windows import package: {package}")
    print("After extracting the ZIP, open Command Prompt in that folder and run:")
    print(f"ollama create {name} -f Modelfile.trained")
    print(f"Then test: ollama run {name}")


if __name__ == "__main__":
    main()
