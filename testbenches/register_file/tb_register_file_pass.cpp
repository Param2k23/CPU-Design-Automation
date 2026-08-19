#include <iostream>
#include <memory>
#include "Vregister_file.h"
#include "verilated.h"

void tick(Vregister_file* top) {
    top->clk = 0;
    top->eval();
    top->clk = 1;
    top->eval();
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Vregister_file>();

    // Test writing to register 5
    top->we = 1;
    top->rd = 5;
    top->wdata = 12345;
    tick(top.get());
    
    // Disable write, read from register 5
    top->we = 0;
    top->rs1 = 5;
    top->eval();

    if (top->rdata1 != 12345) {
        std::cerr << "Assertion failed: Expected 12345 in rdata1 but got " << top->rdata1 << std::endl;
        return 1;
    }

    // Try reading x0 (must be 0)
    top->rs2 = 0;
    top->eval();

    if (top->rdata2 != 0) {
        std::cerr << "Assertion failed: Expected 0 in rdata2 (register x0) but got " << top->rdata2 << std::endl;
        return 1;
    }

    std::cout << "Register File passing tests completed successfully." << std::endl;
    return 0;
}
