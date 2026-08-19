#include <iostream>
#include <memory>
#include "Valu.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Valu>();

    // Test ADD with intentional failure check
    top->a = 10;
    top->b = 20;
    top->op = 0; // ADD
    top->eval();
    
    // Intentionally expecting the wrong result to simulate a failure
    if (top->result != 999) {
        std::cerr << "Assertion failed: Expected 999 but got " << top->result << std::endl;
        return 1;
    }

    return 0;
}
