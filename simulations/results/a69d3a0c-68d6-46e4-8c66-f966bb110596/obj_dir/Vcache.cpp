// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vcache__pch.h"
#include "verilated_vcd_c.h"

//============================================================
// Constructors

Vcache::Vcache(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vcache__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , rst_n{vlSymsp->TOP.rst_n}
    , rd_en{vlSymsp->TOP.rd_en}
    , wr_en{vlSymsp->TOP.wr_en}
    , hit{vlSymsp->TOP.hit}
    , miss{vlSymsp->TOP.miss}
    , addr{vlSymsp->TOP.addr}
    , wdata{vlSymsp->TOP.wdata}
    , rdata{vlSymsp->TOP.rdata}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
    contextp()->traceBaseModelCbAdd(
        [this](VerilatedTraceBaseC* tfp, int levels, int options) { traceBaseModel(tfp, levels, options); });
}

Vcache::Vcache(const char* _vcname__)
    : Vcache(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vcache::~Vcache() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vcache___024root___eval_debug_assertions(Vcache___024root* vlSelf);
#endif  // VL_DEBUG
void Vcache___024root___eval_static(Vcache___024root* vlSelf);
void Vcache___024root___eval_initial(Vcache___024root* vlSelf);
void Vcache___024root___eval_settle(Vcache___024root* vlSelf);
void Vcache___024root___eval(Vcache___024root* vlSelf);

void Vcache::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcache::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vcache___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_activity = true;
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        vlSymsp->__Vm_didInit = true;
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vcache___024root___eval_static(&(vlSymsp->TOP));
        Vcache___024root___eval_initial(&(vlSymsp->TOP));
        Vcache___024root___eval_settle(&(vlSymsp->TOP));
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vcache___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vcache::eventsPending() { return false; }

uint64_t Vcache::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vcache::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vcache___024root___eval_final(Vcache___024root* vlSelf);

VL_ATTR_COLD void Vcache::final() {
    Vcache___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vcache::hierName() const { return vlSymsp->name(); }
const char* Vcache::modelName() const { return "Vcache"; }
unsigned Vcache::threads() const { return 1; }
void Vcache::prepareClone() const { contextp()->prepareClone(); }
void Vcache::atClone() const {
    contextp()->threadPoolpOnClone();
}
std::unique_ptr<VerilatedTraceConfig> Vcache::traceConfig() const {
    return std::unique_ptr<VerilatedTraceConfig>{new VerilatedTraceConfig{false, false, false}};
};

//============================================================
// Trace configuration

void Vcache___024root__trace_decl_types(VerilatedVcd* tracep);

void Vcache___024root__trace_init_top(Vcache___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD static void trace_init(void* voidSelf, VerilatedVcd* tracep, uint32_t code) {
    // Callback from tracep->open()
    Vcache___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vcache___024root*>(voidSelf);
    Vcache__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (!vlSymsp->_vm_contextp__->calcUnusedSigs()) {
        VL_FATAL_MT(__FILE__, __LINE__, __FILE__,
            "Turning on wave traces requires Verilated::traceEverOn(true) call before time 0.");
    }
    vlSymsp->__Vm_baseCode = code;
    tracep->pushPrefix(std::string{vlSymsp->name()}, VerilatedTracePrefixType::SCOPE_MODULE);
    Vcache___024root__trace_decl_types(tracep);
    Vcache___024root__trace_init_top(vlSelf, tracep);
    tracep->popPrefix();
}

VL_ATTR_COLD void Vcache___024root__trace_register(Vcache___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD void Vcache::traceBaseModel(VerilatedTraceBaseC* tfp, int levels, int options) {
    (void)levels; (void)options;
    VerilatedVcdC* const stfp = dynamic_cast<VerilatedVcdC*>(tfp);
    if (VL_UNLIKELY(!stfp)) {
        vl_fatal(__FILE__, __LINE__, __FILE__,"'Vcache::trace()' called on non-VerilatedVcdC object;"
            " use --trace-fst with VerilatedFst object, and --trace with VerilatedVcd object");
    }
    stfp->spTrace()->addModel(this);
    stfp->spTrace()->addInitCb(&trace_init, &(vlSymsp->TOP));
    Vcache___024root__trace_register(&(vlSymsp->TOP), stfp->spTrace());
}
