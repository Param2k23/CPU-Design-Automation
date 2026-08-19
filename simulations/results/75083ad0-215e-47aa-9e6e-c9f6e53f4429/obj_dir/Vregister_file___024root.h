// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vregister_file.h for the primary calling header

#ifndef VERILATED_VREGISTER_FILE___024ROOT_H_
#define VERILATED_VREGISTER_FILE___024ROOT_H_  // guard

#include "verilated.h"


class Vregister_file__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vregister_file___024root final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(we,0,0);
    VL_IN8(rs1,4,0);
    VL_IN8(rs2,4,0);
    VL_IN8(rd,4,0);
    CData/*0:0*/ __VstlFirstIteration;
    CData/*0:0*/ __VicoFirstIteration;
    CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
    CData/*0:0*/ __VactContinue;
    VL_IN(wdata,31,0);
    VL_OUT(rdata1,31,0);
    VL_OUT(rdata2,31,0);
    IData/*31:0*/ __VactIterCount;
    VlUnpacked<IData/*31:0*/, 32> register_file__DOT__regs;
    VlTriggerVec<1> __VstlTriggered;
    VlTriggerVec<1> __VicoTriggered;
    VlTriggerVec<1> __VactTriggered;
    VlTriggerVec<1> __VnbaTriggered;

    // INTERNAL VARIABLES
    Vregister_file__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vregister_file___024root(Vregister_file__Syms* symsp, const char* v__name);
    ~Vregister_file___024root();
    VL_UNCOPYABLE(Vregister_file___024root);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
