#include <iostream>
#include <memory>
#include "Valu.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Valu>();

    Verilated::traceEverOn(true);
    auto trace = std::make_unique<VerilatedVcdC>();
    top->trace(trace.get(), 99);
    trace->open("waveform.vcd");
    int time = 0;

    // Test ADD with intentional failure check
    top->a = 10;
    top->b = 20;
    top->op = 0; // ADD
    top->eval();
    trace->dump(time++);
    
    // Intentionally expecting the wrong result to simulate a failure
    if (top->result != 999) {
        std::cerr << "Assertion failed: Expected 999 but got " << top->result << std::endl;
        trace->close();
        return 1;
    }

    trace->close();
    return 0;
}
