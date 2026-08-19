#include <iostream>
#include <memory>
#include "Valu.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Valu>();

    // Test ADD (op=0)
    top->a = 10;
    top->b = 20;
    top->op = 0;
    top->eval();
    if (top->result != 30) {
        std::cerr << "Assertion failed: ADD 10+20 != " << top->result << std::endl;
        return 1;
    }

    // Test SUB (op=1)
    top->a = 50;
    top->b = 20;
    top->op = 1;
    top->eval();
    if (top->result != 30) {
        std::cerr << "Assertion failed: SUB 50-20 != " << top->result << std::endl;
        return 1;
    }
    
    // Test AND (op=2)
    top->a = 0b1010;
    top->b = 0b1100;
    top->op = 2;
    top->eval();
    if (top->result != 0b1000) {
        std::cerr << "Assertion failed: AND failed" << std::endl;
        return 1;
    }

    std::cout << "All passing tests completed successfully." << std::endl;
    return 0;
}
