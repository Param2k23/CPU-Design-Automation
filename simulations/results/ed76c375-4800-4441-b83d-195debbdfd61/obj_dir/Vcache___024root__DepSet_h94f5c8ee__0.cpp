// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcache.h for the primary calling header

#include "Vcache__pch.h"
#include "Vcache___024root.h"

void Vcache___024root___ico_sequent__TOP__0(Vcache___024root* vlSelf);

void Vcache___024root___eval_ico(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_ico\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((1ULL & vlSelfRef.__VicoTriggered.word(0U))) {
        Vcache___024root___ico_sequent__TOP__0(vlSelf);
    }
}

VL_INLINE_OPT void Vcache___024root___ico_sequent__TOP__0(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___ico_sequent__TOP__0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.hit = ((((IData)(vlSelfRef.rd_en) | (IData)(vlSelfRef.wr_en)) 
                      & vlSelfRef.cache__DOT__cache_valid
                      [(3U & (vlSelfRef.addr >> 2U))]) 
                     & (vlSelfRef.cache__DOT__cache_tag
                        [(3U & (vlSelfRef.addr >> 2U))] 
                        == (vlSelfRef.addr >> 4U)));
    vlSelfRef.miss = ((1U & (~ ((((IData)(vlSelfRef.rd_en) 
                                  | (IData)(vlSelfRef.wr_en)) 
                                 & vlSelfRef.cache__DOT__cache_valid
                                 [(3U & (vlSelfRef.addr 
                                         >> 2U))]) 
                                & (vlSelfRef.cache__DOT__cache_tag
                                   [(3U & (vlSelfRef.addr 
                                           >> 2U))] 
                                   == (vlSelfRef.addr 
                                       >> 4U))))) && 
                      ((IData)(vlSelfRef.rd_en) | (IData)(vlSelfRef.wr_en)));
    vlSelfRef.rdata = (((((IData)(vlSelfRef.rd_en) 
                          | (IData)(vlSelfRef.wr_en)) 
                         & vlSelfRef.cache__DOT__cache_valid
                         [(3U & (vlSelfRef.addr >> 2U))]) 
                        & (vlSelfRef.cache__DOT__cache_tag
                           [(3U & (vlSelfRef.addr >> 2U))] 
                           == (vlSelfRef.addr >> 4U)))
                        ? vlSelfRef.cache__DOT__cache_data
                       [(3U & (vlSelfRef.addr >> 2U))]
                        : (((IData)(vlSelfRef.rd_en) 
                            | (IData)(vlSelfRef.wr_en))
                            ? 0xdeadbeefU : 0U));
}

void Vcache___024root___eval_triggers__ico(Vcache___024root* vlSelf);

bool Vcache___024root___eval_phase__ico(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_phase__ico\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*0:0*/ __VicoExecute;
    // Body
    Vcache___024root___eval_triggers__ico(vlSelf);
    __VicoExecute = vlSelfRef.__VicoTriggered.any();
    if (__VicoExecute) {
        Vcache___024root___eval_ico(vlSelf);
    }
    return (__VicoExecute);
}

void Vcache___024root___eval_act(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_act\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

void Vcache___024root___nba_sequent__TOP__0(Vcache___024root* vlSelf);

void Vcache___024root___eval_nba(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_nba\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((3ULL & vlSelfRef.__VnbaTriggered.word(0U))) {
        Vcache___024root___nba_sequent__TOP__0(vlSelf);
    }
}

VL_INLINE_OPT void Vcache___024root___nba_sequent__TOP__0(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___nba_sequent__TOP__0\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*1:0*/ __VdlyDim0__cache__DOT__cache_valid__v0;
    __VdlyDim0__cache__DOT__cache_valid__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_valid__v0;
    __VdlySet__cache__DOT__cache_valid__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_valid__v1;
    __VdlySet__cache__DOT__cache_valid__v1 = 0;
    IData/*27:0*/ __VdlyVal__cache__DOT__cache_tag__v0;
    __VdlyVal__cache__DOT__cache_tag__v0 = 0;
    CData/*1:0*/ __VdlyDim0__cache__DOT__cache_tag__v0;
    __VdlyDim0__cache__DOT__cache_tag__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_tag__v0;
    __VdlySet__cache__DOT__cache_tag__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_tag__v1;
    __VdlySet__cache__DOT__cache_tag__v1 = 0;
    IData/*31:0*/ __VdlyVal__cache__DOT__cache_data__v0;
    __VdlyVal__cache__DOT__cache_data__v0 = 0;
    CData/*1:0*/ __VdlyDim0__cache__DOT__cache_data__v0;
    __VdlyDim0__cache__DOT__cache_data__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_data__v0;
    __VdlySet__cache__DOT__cache_data__v0 = 0;
    CData/*0:0*/ __VdlySet__cache__DOT__cache_data__v1;
    __VdlySet__cache__DOT__cache_data__v1 = 0;
    // Body
    __VdlySet__cache__DOT__cache_data__v0 = 0U;
    __VdlySet__cache__DOT__cache_data__v1 = 0U;
    __VdlySet__cache__DOT__cache_valid__v0 = 0U;
    __VdlySet__cache__DOT__cache_valid__v1 = 0U;
    __VdlySet__cache__DOT__cache_tag__v0 = 0U;
    __VdlySet__cache__DOT__cache_tag__v1 = 0U;
    if (vlSelfRef.rst_n) {
        if (vlSelfRef.wr_en) {
            __VdlyVal__cache__DOT__cache_data__v0 = vlSelfRef.wdata;
            __VdlyDim0__cache__DOT__cache_data__v0 
                = (3U & (vlSelfRef.addr >> 2U));
            __VdlySet__cache__DOT__cache_data__v0 = 1U;
            __VdlyDim0__cache__DOT__cache_valid__v0 
                = (3U & (vlSelfRef.addr >> 2U));
            __VdlySet__cache__DOT__cache_valid__v0 = 1U;
            __VdlyVal__cache__DOT__cache_tag__v0 = 
                (vlSelfRef.addr >> 4U);
            __VdlyDim0__cache__DOT__cache_tag__v0 = 
                (3U & (vlSelfRef.addr >> 2U));
            __VdlySet__cache__DOT__cache_tag__v0 = 1U;
        }
    } else {
        __VdlySet__cache__DOT__cache_data__v1 = 1U;
        __VdlySet__cache__DOT__cache_valid__v1 = 1U;
        __VdlySet__cache__DOT__cache_tag__v1 = 1U;
    }
    if (__VdlySet__cache__DOT__cache_data__v0) {
        vlSelfRef.cache__DOT__cache_data[__VdlyDim0__cache__DOT__cache_data__v0] 
            = __VdlyVal__cache__DOT__cache_data__v0;
    }
    if (__VdlySet__cache__DOT__cache_data__v1) {
        vlSelfRef.cache__DOT__cache_data[0U] = 0U;
        vlSelfRef.cache__DOT__cache_data[1U] = 0U;
        vlSelfRef.cache__DOT__cache_data[2U] = 0U;
        vlSelfRef.cache__DOT__cache_data[3U] = 0U;
    }
    if (__VdlySet__cache__DOT__cache_valid__v0) {
        vlSelfRef.cache__DOT__cache_valid[__VdlyDim0__cache__DOT__cache_valid__v0] = 1U;
    }
    if (__VdlySet__cache__DOT__cache_valid__v1) {
        vlSelfRef.cache__DOT__cache_valid[0U] = 0U;
        vlSelfRef.cache__DOT__cache_valid[1U] = 0U;
        vlSelfRef.cache__DOT__cache_valid[2U] = 0U;
        vlSelfRef.cache__DOT__cache_valid[3U] = 0U;
    }
    if (__VdlySet__cache__DOT__cache_tag__v0) {
        vlSelfRef.cache__DOT__cache_tag[__VdlyDim0__cache__DOT__cache_tag__v0] 
            = __VdlyVal__cache__DOT__cache_tag__v0;
    }
    if (__VdlySet__cache__DOT__cache_tag__v1) {
        vlSelfRef.cache__DOT__cache_tag[0U] = 0U;
        vlSelfRef.cache__DOT__cache_tag[1U] = 0U;
        vlSelfRef.cache__DOT__cache_tag[2U] = 0U;
        vlSelfRef.cache__DOT__cache_tag[3U] = 0U;
    }
    vlSelfRef.hit = ((((IData)(vlSelfRef.rd_en) | (IData)(vlSelfRef.wr_en)) 
                      & vlSelfRef.cache__DOT__cache_valid
                      [(3U & (vlSelfRef.addr >> 2U))]) 
                     & (vlSelfRef.cache__DOT__cache_tag
                        [(3U & (vlSelfRef.addr >> 2U))] 
                        == (vlSelfRef.addr >> 4U)));
    vlSelfRef.miss = ((1U & (~ ((((IData)(vlSelfRef.rd_en) 
                                  | (IData)(vlSelfRef.wr_en)) 
                                 & vlSelfRef.cache__DOT__cache_valid
                                 [(3U & (vlSelfRef.addr 
                                         >> 2U))]) 
                                & (vlSelfRef.cache__DOT__cache_tag
                                   [(3U & (vlSelfRef.addr 
                                           >> 2U))] 
                                   == (vlSelfRef.addr 
                                       >> 4U))))) && 
                      ((IData)(vlSelfRef.rd_en) | (IData)(vlSelfRef.wr_en)));
    vlSelfRef.rdata = (((((IData)(vlSelfRef.rd_en) 
                          | (IData)(vlSelfRef.wr_en)) 
                         & vlSelfRef.cache__DOT__cache_valid
                         [(3U & (vlSelfRef.addr >> 2U))]) 
                        & (vlSelfRef.cache__DOT__cache_tag
                           [(3U & (vlSelfRef.addr >> 2U))] 
                           == (vlSelfRef.addr >> 4U)))
                        ? vlSelfRef.cache__DOT__cache_data
                       [(3U & (vlSelfRef.addr >> 2U))]
                        : (((IData)(vlSelfRef.rd_en) 
                            | (IData)(vlSelfRef.wr_en))
                            ? 0xdeadbeefU : 0U));
}

void Vcache___024root___eval_triggers__act(Vcache___024root* vlSelf);

bool Vcache___024root___eval_phase__act(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_phase__act\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    VlTriggerVec<2> __VpreTriggered;
    CData/*0:0*/ __VactExecute;
    // Body
    Vcache___024root___eval_triggers__act(vlSelf);
    __VactExecute = vlSelfRef.__VactTriggered.any();
    if (__VactExecute) {
        __VpreTriggered.andNot(vlSelfRef.__VactTriggered, vlSelfRef.__VnbaTriggered);
        vlSelfRef.__VnbaTriggered.thisOr(vlSelfRef.__VactTriggered);
        Vcache___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

bool Vcache___024root___eval_phase__nba(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_phase__nba\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = vlSelfRef.__VnbaTriggered.any();
    if (__VnbaExecute) {
        Vcache___024root___eval_nba(vlSelf);
        vlSelfRef.__VnbaTriggered.clear();
    }
    return (__VnbaExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__ico(Vcache___024root* vlSelf);
#endif  // VL_DEBUG
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__nba(Vcache___024root* vlSelf);
#endif  // VL_DEBUG
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcache___024root___dump_triggers__act(Vcache___024root* vlSelf);
#endif  // VL_DEBUG

void Vcache___024root___eval(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Init
    IData/*31:0*/ __VicoIterCount;
    CData/*0:0*/ __VicoContinue;
    IData/*31:0*/ __VnbaIterCount;
    CData/*0:0*/ __VnbaContinue;
    // Body
    __VicoIterCount = 0U;
    vlSelfRef.__VicoFirstIteration = 1U;
    __VicoContinue = 1U;
    while (__VicoContinue) {
        if (VL_UNLIKELY((0x64U < __VicoIterCount))) {
#ifdef VL_DEBUG
            Vcache___024root___dump_triggers__ico(vlSelf);
#endif
            VL_FATAL_MT("/app/rtl/cache/cache.sv", 1, "", "Input combinational region did not converge.");
        }
        __VicoIterCount = ((IData)(1U) + __VicoIterCount);
        __VicoContinue = 0U;
        if (Vcache___024root___eval_phase__ico(vlSelf)) {
            __VicoContinue = 1U;
        }
        vlSelfRef.__VicoFirstIteration = 0U;
    }
    __VnbaIterCount = 0U;
    __VnbaContinue = 1U;
    while (__VnbaContinue) {
        if (VL_UNLIKELY((0x64U < __VnbaIterCount))) {
#ifdef VL_DEBUG
            Vcache___024root___dump_triggers__nba(vlSelf);
#endif
            VL_FATAL_MT("/app/rtl/cache/cache.sv", 1, "", "NBA region did not converge.");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        __VnbaContinue = 0U;
        vlSelfRef.__VactIterCount = 0U;
        vlSelfRef.__VactContinue = 1U;
        while (vlSelfRef.__VactContinue) {
            if (VL_UNLIKELY((0x64U < vlSelfRef.__VactIterCount))) {
#ifdef VL_DEBUG
                Vcache___024root___dump_triggers__act(vlSelf);
#endif
                VL_FATAL_MT("/app/rtl/cache/cache.sv", 1, "", "Active region did not converge.");
            }
            vlSelfRef.__VactIterCount = ((IData)(1U) 
                                         + vlSelfRef.__VactIterCount);
            vlSelfRef.__VactContinue = 0U;
            if (Vcache___024root___eval_phase__act(vlSelf)) {
                vlSelfRef.__VactContinue = 1U;
            }
        }
        if (Vcache___024root___eval_phase__nba(vlSelf)) {
            __VnbaContinue = 1U;
        }
    }
}

#ifdef VL_DEBUG
void Vcache___024root___eval_debug_assertions(Vcache___024root* vlSelf) {
    (void)vlSelf;  // Prevent unused variable warning
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcache___024root___eval_debug_assertions\n"); );
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY((vlSelfRef.clk & 0xfeU))) {
        Verilated::overWidthError("clk");}
    if (VL_UNLIKELY((vlSelfRef.rst_n & 0xfeU))) {
        Verilated::overWidthError("rst_n");}
    if (VL_UNLIKELY((vlSelfRef.rd_en & 0xfeU))) {
        Verilated::overWidthError("rd_en");}
    if (VL_UNLIKELY((vlSelfRef.wr_en & 0xfeU))) {
        Verilated::overWidthError("wr_en");}
}
#endif  // VL_DEBUG
