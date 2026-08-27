// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Tracing implementation internals
#include "verilated_vcd_c.h"
#include "Vregister_file__Syms.h"


VL_ATTR_COLD void Vregister_file___024root__trace_init_sub__TOP__0(Vregister_file___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_init_sub__TOP__0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    const int c = vlSymsp->__Vm_baseCode;
    // Body
    tracep->declBit(c+33,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+34,0,"we",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+35,0,"rs1",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+36,0,"rs2",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+37,0,"rd",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+38,0,"wdata",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+39,0,"rdata1",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+40,0,"rdata2",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("register_file", VerilatedTracePrefixType::SCOPE_MODULE);
    tracep->declBit(c+33,0,"clk",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBit(c+34,0,"we",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1);
    tracep->declBus(c+35,0,"rs1",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+36,0,"rs2",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+37,0,"rd",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 4,0);
    tracep->declBus(c+38,0,"wdata",-1, VerilatedTraceSigDirection::INPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+39,0,"rdata1",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->declBus(c+40,0,"rdata2",-1, VerilatedTraceSigDirection::OUTPUT, VerilatedTraceSigKind::WIRE, VerilatedTraceSigType::LOGIC, false,-1, 31,0);
    tracep->pushPrefix("regs", VerilatedTracePrefixType::ARRAY_UNPACKED);
    for (int i = 0; i < 32; ++i) {
        tracep->declBus(c+1+i*1,0,"",-1, VerilatedTraceSigDirection::NONE, VerilatedTraceSigKind::VAR, VerilatedTraceSigType::LOGIC, true,(i+0), 31,0);
    }
    tracep->popPrefix();
    tracep->popPrefix();
}

VL_ATTR_COLD void Vregister_file___024root__trace_init_top(Vregister_file___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_init_top\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    Vregister_file___024root__trace_init_sub__TOP__0(vlSelf, tracep);
}

VL_ATTR_COLD void Vregister_file___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
VL_ATTR_COLD void Vregister_file___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void Vregister_file___024root__trace_chg_0(void* voidSelf, VerilatedVcd::Buffer* bufp);
void Vregister_file___024root__trace_cleanup(void* voidSelf, VerilatedVcd* /*unused*/);

VL_ATTR_COLD void Vregister_file___024root__trace_register(Vregister_file___024root* vlSelf, VerilatedVcd* tracep) {
    (void)vlSelf;  // Prevent unused variable warning
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_register\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    tracep->addConstCb(&Vregister_file___024root__trace_const_0, 0U, vlSelf);
    tracep->addFullCb(&Vregister_file___024root__trace_full_0, 0U, vlSelf);
    tracep->addChgCb(&Vregister_file___024root__trace_chg_0, 0U, vlSelf);
    tracep->addCleanupCb(&Vregister_file___024root__trace_cleanup, vlSelf);
}

VL_ATTR_COLD void Vregister_file___024root__trace_const_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_const_0\n"); );
    // Init
    Vregister_file___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vregister_file___024root*>(voidSelf);
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
}

VL_ATTR_COLD void Vregister_file___024root__trace_full_0_sub_0(Vregister_file___024root* vlSelf, VerilatedVcd::Buffer* bufp);

VL_ATTR_COLD void Vregister_file___024root__trace_full_0(void* voidSelf, VerilatedVcd::Buffer* bufp) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_full_0\n"); );
    // Init
    Vregister_file___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vregister_file___024root*>(voidSelf);
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    // Body
    Vregister_file___024root__trace_full_0_sub_0((&vlSymsp->TOP), bufp);
}

VL_ATTR_COLD void Vregister_file___024root__trace_full_0_sub_0(Vregister_file___024root* vlSelf, VerilatedVcd::Buffer* bufp) {
    (void)vlSelf;  // Prevent unused variable warning
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vregister_file___024root__trace_full_0_sub_0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    uint32_t* const oldp VL_ATTR_UNUSED = bufp->oldp(vlSymsp->__Vm_baseCode);
    // Body
    bufp->fullIData(oldp+1,(vlSelfRef.register_file__DOT__regs[0]),32);
    bufp->fullIData(oldp+2,(vlSelfRef.register_file__DOT__regs[1]),32);
    bufp->fullIData(oldp+3,(vlSelfRef.register_file__DOT__regs[2]),32);
    bufp->fullIData(oldp+4,(vlSelfRef.register_file__DOT__regs[3]),32);
    bufp->fullIData(oldp+5,(vlSelfRef.register_file__DOT__regs[4]),32);
    bufp->fullIData(oldp+6,(vlSelfRef.register_file__DOT__regs[5]),32);
    bufp->fullIData(oldp+7,(vlSelfRef.register_file__DOT__regs[6]),32);
    bufp->fullIData(oldp+8,(vlSelfRef.register_file__DOT__regs[7]),32);
    bufp->fullIData(oldp+9,(vlSelfRef.register_file__DOT__regs[8]),32);
    bufp->fullIData(oldp+10,(vlSelfRef.register_file__DOT__regs[9]),32);
    bufp->fullIData(oldp+11,(vlSelfRef.register_file__DOT__regs[10]),32);
    bufp->fullIData(oldp+12,(vlSelfRef.register_file__DOT__regs[11]),32);
    bufp->fullIData(oldp+13,(vlSelfRef.register_file__DOT__regs[12]),32);
    bufp->fullIData(oldp+14,(vlSelfRef.register_file__DOT__regs[13]),32);
    bufp->fullIData(oldp+15,(vlSelfRef.register_file__DOT__regs[14]),32);
    bufp->fullIData(oldp+16,(vlSelfRef.register_file__DOT__regs[15]),32);
    bufp->fullIData(oldp+17,(vlSelfRef.register_file__DOT__regs[16]),32);
    bufp->fullIData(oldp+18,(vlSelfRef.register_file__DOT__regs[17]),32);
    bufp->fullIData(oldp+19,(vlSelfRef.register_file__DOT__regs[18]),32);
    bufp->fullIData(oldp+20,(vlSelfRef.register_file__DOT__regs[19]),32);
    bufp->fullIData(oldp+21,(vlSelfRef.register_file__DOT__regs[20]),32);
    bufp->fullIData(oldp+22,(vlSelfRef.register_file__DOT__regs[21]),32);
    bufp->fullIData(oldp+23,(vlSelfRef.register_file__DOT__regs[22]),32);
    bufp->fullIData(oldp+24,(vlSelfRef.register_file__DOT__regs[23]),32);
    bufp->fullIData(oldp+25,(vlSelfRef.register_file__DOT__regs[24]),32);
    bufp->fullIData(oldp+26,(vlSelfRef.register_file__DOT__regs[25]),32);
    bufp->fullIData(oldp+27,(vlSelfRef.register_file__DOT__regs[26]),32);
    bufp->fullIData(oldp+28,(vlSelfRef.register_file__DOT__regs[27]),32);
    bufp->fullIData(oldp+29,(vlSelfRef.register_file__DOT__regs[28]),32);
    bufp->fullIData(oldp+30,(vlSelfRef.register_file__DOT__regs[29]),32);
    bufp->fullIData(oldp+31,(vlSelfRef.register_file__DOT__regs[30]),32);
    bufp->fullIData(oldp+32,(vlSelfRef.register_file__DOT__regs[31]),32);
    bufp->fullBit(oldp+33,(vlSelfRef.clk));
    bufp->fullBit(oldp+34,(vlSelfRef.we));
    bufp->fullCData(oldp+35,(vlSelfRef.rs1),5);
    bufp->fullCData(oldp+36,(vlSelfRef.rs2),5);
    bufp->fullCData(oldp+37,(vlSelfRef.rd),5);
    bufp->fullIData(oldp+38,(vlSelfRef.wdata),32);
    bufp->fullIData(oldp+39,(vlSelfRef.rdata1),32);
    bufp->fullIData(oldp+40,(vlSelfRef.rdata2),32);
}
