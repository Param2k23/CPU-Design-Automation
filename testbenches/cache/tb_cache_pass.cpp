#include <iostream>
#include <memory>
#include "Vcache.h"
#include "verilated.h"

void tick(Vcache* top) {
    top->clk = 0;
    top->eval();
    top->clk = 1;
    top->eval();
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Vcache>();

    // Reset
    top->rst_n = 0;
    tick(top.get());
    top->rst_n = 1;
    tick(top.get());

    // Test a read miss initially
    top->rd_en = 1;
    top->addr = 0x1000;
    top->eval();

    if (!top->miss) {
        std::cerr << "Assertion failed: Expected initial miss" << std::endl;
        return 1;
    }

    // Write data to address 0x1000
    top->rd_en = 0;
    top->wr_en = 1;
    top->addr = 0x1000;
    top->wdata = 0xabcdef01;
    tick(top.get());

    // Read address 0x1000 again (should be hit)
    top->wr_en = 0;
    top->rd_en = 1;
    top->addr = 0x1000;
    top->eval();

    if (!top->hit) {
        std::cerr << "Assertion failed: Expected hit for address 0x1000" << std::endl;
        return 1;
    }

    if (top->rdata != 0xabcdef01) {
        std::cerr << "Assertion failed: Expected 0xabcdef01 but got " << std::hex << top->rdata << std::endl;
        return 1;
    }

    std::cout << "Cache passing tests completed successfully." << std::endl;
    return 0;
}
