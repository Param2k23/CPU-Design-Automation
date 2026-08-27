// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals
#include "verilated_vcd_c.h"
#include "Vregister_file__Syms.h"


void Vregister_file___024root__trace_chg_0_sub_0(Vregister_file___024root* vlSelf, VerilatedVcd::Buffer* bufp);

void Vregister_file___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_chg_0\n"); );
    // Init
    Vregister_file___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vregister_file___024root*>(voidSelf);
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (VL_UNLIKELY(!vlSymsp->__Vm_activity)) return;
    // Body
    Vregister_file___024root__trace_chg_0_sub_0((&vlSymsp->TOP), bufp);
}

void Vregister_file___024root__trace_chg_0_sub_0(Vregister_file___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    (void)vlSelf;  // Prevent unused variable warning
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_chg_0_sub_0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode + 1);
    // Body
    if (VL_UNLIKELY(vlSelfRef.__Vm_traceActivity[1U])) {
        bufp->chgIData(oldp+0,(vlSelfRef.register_file__DOT__regs[0]),32);
        bufp->chgIData(oldp+1,(vlSelfRef.register_file__DOT__regs[1]),32);
        bufp->chgIData(oldp+2,(vlSelfRef.register_file__DOT__regs[2]),32);
        bufp->chgIData(oldp+3,(vlSelfRef.register_file__DOT__regs[3]),32);
        bufp->chgIData(oldp+4,(vlSelfRef.register_file__DOT__regs[4]),32);
        bufp->chgIData(oldp+5,(vlSelfRef.register_file__DOT__regs[5]),32);
        bufp->chgIData(oldp+6,(vlSelfRef.register_file__DOT__regs[6]),32);
        bufp->chgIData(oldp+7,(vlSelfRef.register_file__DOT__regs[7]),32);
        bufp->chgIData(oldp+8,(vlSelfRef.register_file__DOT__regs[8]),32);
        bufp->chgIData(oldp+9,(vlSelfRef.register_file__DOT__regs[9]),32);
        bufp->chgIData(oldp+10,(vlSelfRef.register_file__DOT__regs[10]),32);
        bufp->chgIData(oldp+11,(vlSelfRef.register_file__DOT__regs[11]),32);
        bufp->chgIData(oldp+12,(vlSelfRef.register_file__DOT__regs[12]),32);
        bufp->chgIData(oldp+13,(vlSelfRef.register_file__DOT__regs[13]),32);
        bufp->chgIData(oldp+14,(vlSelfRef.register_file__DOT__regs[14]),32);
        bufp->chgIData(oldp+15,(vlSelfRef.register_file__DOT__regs[15]),32);
        bufp->chgIData(oldp+16,(vlSelfRef.register_file__DOT__regs[16]),32);
        bufp->chgIData(oldp+17,(vlSelfRef.register_file__DOT__regs[17]),32);
        bufp->chgIData(oldp+18,(vlSelfRef.register_file__DOT__regs[18]),32);
        bufp->chgIData(oldp+19,(vlSelfRef.register_file__DOT__regs[19]),32);
        bufp->chgIData(oldp+20,(vlSelfRef.register_file__DOT__regs[20]),32);
        bufp->chgIData(oldp+21,(vlSelfRef.register_file__DOT__regs[21]),32);
        bufp->chgIData(oldp+22,(vlSelfRef.register_file__DOT__regs[22]),32);
        bufp->chgIData(oldp+23,(vlSelfRef.register_file__DOT__regs[23]),32);
        bufp->chgIData(oldp+24,(vlSelfRef.register_file__DOT__regs[24]),32);
        bufp->chgIData(oldp+25,(vlSelfRef.register_file__DOT__regs[25]),32);
        bufp->chgIData(oldp+26,(vlSelfRef.register_file__DOT__regs[26]),32);
        bufp->chgIData(oldp+27,(vlSelfRef.register_file__DOT__regs[27]),32);
        bufp->chgIData(oldp+28,(vlSelfRef.register_file__DOT__regs[28]),32);
        bufp->chgIData(oldp+29,(vlSelfRef.register_file__DOT__regs[29]),32);
        bufp->chgIData(oldp+30,(vlSelfRef.register_file__DOT__regs[30]),32);
        bufp->chgIData(oldp+31,(vlSelfRef.register_file__DOT__regs[31]),32);
    }
    bufp->chgBit(oldp+32,(vlSelfRef.clk));
    bufp->chgBit(oldp+33,(vlSelfRef.we));
    bufp->chgCData(oldp+34,(vlSelfRef.rs1),5);
    bufp->chgCData(oldp+35,(vlSelfRef.rs2),5);
    bufp->chgCData(oldp+36,(vlSelfRef.rd),5);
    bufp->chgIData(oldp+37,(vlSelfRef.wdata),32);
    bufp->chgIData(oldp+38,(vlSelfRef.rdata1),32);
    bufp->chgIData(oldp+39,(vlSelfRef.rdata2),32);
}

void Vregister_file___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_cleanup\n"); );
    // Init
    Vregister_file___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vregister_file___024root*>(voidSelf);
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    // Body
    vlSymsp->__Vm_activity = false;
    vlSymsp->TOP.__Vm_traceActivity[0U] = 0U;
    vlSymsp->TOP.__Vm_traceActivity[1U] = 0U;
}
