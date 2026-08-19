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
    top->wr_en = 0;
    top->rd_en = 0;
    tick(top.get());
    top->rst_n = 1;
    tick(top.get());

    if (!top->empty) {
        std::cerr << "Assertion failed: FIFO not empty after reset" << std::endl;
        return 1;
    }

    // Write a value
    top->din = 42;
    top->wr_en = 1;
    tick(top.get());
    top->wr_en = 0;

    if (top->empty) {
        std::cerr << "Assertion failed: FIFO empty after write" << std::endl;
        return 1;
    }

    // Read the value
    top->rd_en = 1;
    tick(top.get());
    top->rd_en = 0;

    if (top->dout != 42) {
        std::cerr << "Assertion failed: Expected 42 but got " << top->dout << std::endl;
        return 1;
    }

    std::cout << "FIFO passing tests completed successfully." << std::endl;
    return 0;
}
