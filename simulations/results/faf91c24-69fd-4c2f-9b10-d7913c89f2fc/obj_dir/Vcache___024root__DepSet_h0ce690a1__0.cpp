// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcache.h for the primary calling header

#include "Vcache__pch.h"
#include "Vcache__Syms.h"
#include "Vcache___024root.h"

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__ico(Vcache___024root* vlSelf);
#endif  // VL_DEBUG

void Vcache___024root___eval_triggers__ico(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_triggers__ico\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VicoTriggered.set(0U, (IData)(vlSelfRef.__VicoFirstIteration));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcache___024root___dump_triggers__ico(vlSelf);
    }
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__act(Vcache___024root* vlSelf);
#endif  // VL_DEBUG

void Vcache___024root___eval_triggers__act(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_triggers__act\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VactTriggered.set(0U, ((IData)(vlSelfRef.clk) 
                                       & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__0))));
    vlSelfRef.__VactTriggered.set(1U, ((~ (IData)(vlSelfRef.rst_n)) 
                                       & (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rst_n__0)));
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__rst_n__0 = vlSelfRef.rst_n;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcache___024root___dump_triggers__act(vlSelf);
    }
#endif
}
