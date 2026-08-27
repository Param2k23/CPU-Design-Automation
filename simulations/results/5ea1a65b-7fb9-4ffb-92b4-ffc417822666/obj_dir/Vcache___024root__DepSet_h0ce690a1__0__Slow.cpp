// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcache.h for the primary calling header

#include "Vcache__pch.h"
#include "Vcache__Syms.h"
#include "Vcache___024root.h"

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__stl(Vcache___024root* vlSelf);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcache___024root___eval_triggers__stl(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_triggers__stl\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VstlTriggered.set(0U, (IData)(vlSelfRef.__VstlFirstIteration));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcache___024root___dump_triggers__stl(vlSelf);
    }
#endif
}
