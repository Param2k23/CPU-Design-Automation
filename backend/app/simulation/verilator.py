import subprocess
import os
import time

def run_verilator(rtl_path: str, testbench_path: str, output_dir: str, coverage_enabled: bool = False):
    """
    Run Verilator on the given RTL and testbench safely.
    Returns (exit_code, stdout, stderr, runtime_ms)
    """
    start_time = time.time()
    
    # We construct the command carefully, avoiding shell=True.
    # The output directory for verilator obj_dir is set.
    obj_dir = os.path.join(output_dir, "obj_dir")
    
    # Example compile command for Verilator
    # verilator --cc <rtl> --exe <testbench> -Mdir <obj_dir> --build
    compile_cmd = [
        "verilator",
        "--trace",
        "--cc", rtl_path,
        "--exe", testbench_path,
        "-Mdir", obj_dir,
        "--build",
        "-Wall" # Enable all warnings, helps with failure detection
    ]
    if coverage_enabled:
        compile_cmd.append("--coverage")
    
    try:
        compile_result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=60 # 60 second compilation timeout
        )
    except subprocess.TimeoutExpired as e:
        runtime_ms = int((time.time() - start_time) * 1000)
        return (-1, e.stdout.decode() if e.stdout else "", "Compilation Timeout", runtime_ms)
        
    if compile_result.returncode != 0:
        runtime_ms = int((time.time() - start_time) * 1000)
        return (compile_result.returncode, compile_result.stdout, compile_result.stderr, runtime_ms)
        
    # Example execution command
    # The executable is named after the RTL file. e.g. V<rtl_basename>
    rtl_basename = os.path.splitext(os.path.basename(rtl_path))[0]
    exe_path = os.path.join(obj_dir, f"V{rtl_basename}")
    
    try:
        sim_result = subprocess.run(
            [exe_path],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=120 # 2 minute simulation timeout
        )
    except subprocess.TimeoutExpired as e:
        runtime_ms = int((time.time() - start_time) * 1000)
        return (-2, e.stdout.decode() if e.stdout else "", "Simulation Timeout", runtime_ms)

    runtime_ms = int((time.time() - start_time) * 1000)
    
    # Combine compile and sim outputs for the final logs
    stdout = f"--- COMPILE STDOUT ---\n{compile_result.stdout}\n--- SIMULATION STDOUT ---\n{sim_result.stdout}"
    stderr = f"--- COMPILE STDERR ---\n{compile_result.stderr}\n--- SIMULATION STDERR ---\n{sim_result.stderr}"

    return (sim_result.returncode, stdout, stderr, runtime_ms)

def classify_failure(exit_code: int, stdout: str, stderr: str) -> str:
    if exit_code == 0:
        return None
    if exit_code == -1:
        return "TIMEOUT"
    if exit_code == -2:
        return "TIMEOUT"
        
    stderr_lower = stderr.lower()
    stdout_lower = stdout.lower()
    
    if "syntax error" in stderr_lower or "error:" in stderr_lower and "verilator" in stderr_lower:
        return "COMPILE_ERROR"
        
    if "assert" in stderr_lower or "assert" in stdout_lower or "assertion" in stderr_lower or "assertion" in stdout_lower:
        return "ASSERTION_FAILURE"
        
    if exit_code != 0:
        return "SIMULATION_ERROR"
        
    return "UNKNOWN"
