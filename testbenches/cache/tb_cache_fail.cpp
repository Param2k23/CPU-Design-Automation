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

    // Write data to address 0x1000
    top->wr_en = 1;
    top->addr = 0x1000;
    top->wdata = 0xabcdef01;
    tick(top.get());

    // Read address 0x1000 again (should hit, but we intentionally assert it's a miss to simulate failure)
    top->wr_en = 0;
    top->rd_en = 1;
    top->addr = 0x1000;
    top->eval();

    if (top->hit) {
        std::cerr << "Assertion failed: Expected hit to be false (intentional failure)" << std::endl;
        return 1;
    }

    return 0;
}
