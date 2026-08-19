// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vcache.h for the primary calling header

#ifndef VERILATED_VCACHE___024ROOT_H_
#define VERILATED_VCACHE___024ROOT_H_  // guard

#include "verilated.h"


class Vcache__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vcache___024root final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(rst_n,0,0);
    VL_IN8(rd_en,0,0);
    VL_IN8(wr_en,0,0);
    VL_OUT8(hit,0,0);
    VL_OUT8(miss,0,0);
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
    CData/*0:0*/ __Vtrigprevexpr___TOP__rst_n__0;
    CData/*0:0*/ __VactContinue;
    VL_IN(addr,31,0);
    VL_IN(wdata,31,0);
    VL_OUT(rdata,31,0);
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<IData/*31:0*/, 4> cache__DOT__cache_data;
    VlUnpacked<IData/*27:0*/, 4> cache__DOT__cache_tag;
    VlUnpacked<CData/*0:0*/, 4> cache__DOT__cache_valid;
    VlTriggerVec<1> __VstlTriggered;
    VlTriggerVec<1> __VicoTriggered;
    VlTriggerVec<2> __VactTriggered;
    VlTriggerVec<2> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vcache__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vcache___024root(Vcache__Syms* symsp, const char* v__name);
    ~Vcache___024root();
    VL_UNCOPYABLE(Vcache___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
