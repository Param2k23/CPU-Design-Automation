// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcache.h for the primary calling header

#include "Vcache__pch.h"
#include "Vcache__Syms.h"
#include "Vcache___024root.h"

void Vcache___024root___ctor_var_reset(Vcache___024root* vlSelf);

Vcache___024root::Vcache___024root(Vcache__Syms* symsp, const char* v__name)
    : VerilatedModule{v__name}
    , vlSymsp{symsp}
 {
    // Reset structure values
    Vcache___024root___ctor_var_reset(this);
}

void Vcache___024root::__Vconfigure(bool first) {
    (void)first;  // Prevent unused variable warning
}

Vcache___024root::~Vcache___024root() {
}
