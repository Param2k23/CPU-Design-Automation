#include <iostream>
#include <memory>
#include "Vfifo.h"
#include "verilated.h"

void tick(Vfifo* top) {
    top->clk = 0;
    top->eval();
    top->clk = 1;
    top->eval();
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    auto top = std::make_unique<Vfifo>();

    // Reset
    top->rst_n = 0;
    tick(top.get());
    top->rst_n = 1;
    tick(top.get());

    // Write a value
    top->din = 42;
    top->wr_en = 1;
    tick(top.get());
    top->wr_en = 0;

    // Read it, but assert it returns 999 instead of 42
    top->rd_en = 1;
    tick(top.get());
    top->rd_en = 0;

    if (top->dout != 999) {
        std::cerr << "Assertion failed: Expected 999 but got " << top->dout << std::endl;
        return 1;
    }

    return 0;
}
