// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals
#include "verilated_vcd_c.h"
#include "Vcache__Syms.h"


void Vcache___024root__trace_chg_0_sub_0(Vcache___024root* vlSelf, VerilatedVcd::Buffer* bufp);

void Vcache___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root__trace_chg_0\n"); );
    // Init
    Vcache___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vcache___024root*>(voidSelf);
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (VL_UNLIKELY(!vlSymsp->__Vm_activity)) return;
    // Body
    Vcache___024root__trace_chg_0_sub_0((&vlSymsp->TOP), bufp);
}

void Vcache___024root__trace_chg_0_sub_0(Vcache___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root__trace_chg_0_sub_0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode + 1);
    // Body
    if (VL_UNLIKELY(vlSelfRef.__Vm_traceActivity[1U])) {
        bufp->chgIData(oldp+0,(vlSelfRef.cache__DOT__cache_data[0]),32);
        bufp->chgIData(oldp+1,(vlSelfRef.cache__DOT__cache_data[1]),32);
        bufp->chgIData(oldp+2,(vlSelfRef.cache__DOT__cache_data[2]),32);
        bufp->chgIData(oldp+3,(vlSelfRef.cache__DOT__cache_data[3]),32);
        bufp->chgIData(oldp+4,(vlSelfRef.cache__DOT__cache_tag[0]),28);
        bufp->chgIData(oldp+5,(vlSelfRef.cache__DOT__cache_tag[1]),28);
        bufp->chgIData(oldp+6,(vlSelfRef.cache__DOT__cache_tag[2]),28);
        bufp->chgIData(oldp+7,(vlSelfRef.cache__DOT__cache_tag[3]),28);
        bufp->chgBit(oldp+8,(vlSelfRef.cache__DOT__cache_valid[0]));
        bufp->chgBit(oldp+9,(vlSelfRef.cache__DOT__cache_valid[1]));
        bufp->chgBit(oldp+10,(vlSelfRef.cache__DOT__cache_valid[2]));
        bufp->chgBit(oldp+11,(vlSelfRef.cache__DOT__cache_valid[3]));
        bufp->chgIData(oldp+12,(vlSelfRef.cache__DOT__unnamedblk1__DOT__i),32);
    }
    bufp->chgBit(oldp+13,(vlSelfRef.clk));
    bufp->chgBit(oldp+14,(vlSelfRef.rst_n));
    bufp->chgBit(oldp+15,(vlSelfRef.rd_en));
    bufp->chgBit(oldp+16,(vlSelfRef.wr_en));
    bufp->chgIData(oldp+17,(vlSelfRef.addr),32);
    bufp->chgIData(oldp+18,(vlSelfRef.wdata),32);
    bufp->chgIData(oldp+19,(vlSelfRef.rdata),32);
    bufp->chgBit(oldp+20,(vlSelfRef.hit));
    bufp->chgBit(oldp+21,(vlSelfRef.miss));
    bufp->chgCData(oldp+22,((3U & (vlSelfRef.addr >> 2U))),2);
    bufp->chgIData(oldp+23,((vlSelfRef.addr >> 4U)),28);
}

void Vcache___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root__trace_cleanup\n"); );
    // Init
    Vcache___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vcache___024root*>(voidSelf);
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    // Body
    vlSymsp->__Vm_activity = false;
    vlSymsp->TOP.__Vm_traceActivity[0U] = 0U;
    vlSymsp->TOP.__Vm_traceActivity[1U] = 0U;
}
