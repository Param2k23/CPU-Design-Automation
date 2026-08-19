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

    // Intentional failure checking for 999 instead of 12345
    if (top->rdata1 != 999) {
        std::cerr << "Assertion failed: Expected 999 in rdata1 but got " << top->rdata1 << std::endl;
        return 1;
    }

    return 0;
}
