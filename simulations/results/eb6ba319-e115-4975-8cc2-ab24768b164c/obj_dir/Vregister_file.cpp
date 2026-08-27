// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vregister_file__pch.h"
#include "verilated_vcd_c.h"

//============================================================
// Constructors

Vregister_file::Vregister_file(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vregister_file__Syms(contextp(), _vcname__, this)}
    , clk{vlSymsp->TOP.clk}
    , we{vlSymsp->TOP.we}
    , rs1{vlSymsp->TOP.rs1}
    , rs2{vlSymsp->TOP.rs2}
    , rd{vlSymsp->TOP.rd}
    , wdata{vlSymsp->TOP.wdata}
    , rdata1{vlSymsp->TOP.rdata1}
    , rdata2{vlSymsp->TOP.rdata2}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
    contextp()->traceBaseModelCbAdd(
        [this](VerilatedTraceBaseC* tfp, int levels, int options) { traceBaseModel(tfp, levels, options); });
}

Vregister_file::Vregister_file(const char* _vcname__)
    : Vregister_file(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vregister_file::~Vregister_file() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vregister_file___024root___eval_debug_assertions(Vregister_file___024root* vlSelf);
#endif  // VL_DEBUG
void Vregister_file___024root___eval_static(Vregister_file___024root* vlSelf);
void Vregister_file___024root___eval_initial(Vregister_file___024root* vlSelf);
void Vregister_file___024root___eval_settle(Vregister_file___024root* vlSelf);
void Vregister_file___024root___eval(Vregister_file___024root* vlSelf);

void Vregister_file::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vregister_file::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vregister_file___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_activity = true;
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        vlSymsp->__Vm_didInit = true;
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vregister_file___024root___eval_static(&(vlSymsp->TOP));
        Vregister_file___024root___eval_initial(&(vlSymsp->TOP));
        Vregister_file___024root___eval_settle(&(vlSymsp->TOP));
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vregister_file___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vregister_file::eventsPending() { return false; }

uint64_t Vregister_file::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vregister_file::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vregister_file___024root___eval_final(Vregister_file___024root* vlSelf);

VL_ATTR_COLD void Vregister_file::final() {
    Vregister_file___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vregister_file::hierName() const { return vlSymsp->name(); }
const char* Vregister_file::modelName() const { return "Vregister_file"; }
unsigned Vregister_file::threads() const { return 1; }
void Vregister_file::prepareClone() const { contextp()->prepareClone(); }
void Vregister_file::atClone() const {
    contextp()->threadPoolpOnClone();
}
std::unique_ptr<VerilatedTraceConfig> Vregister_file::traceConfig() const {
    return std::unique_ptr<VerilatedTraceConfig>{new VerilatedTraceConfig{false, false, false}};
};

//============================================================
// Trace configuration

void Vregister_file___024root__trace_decl_types(VerilatedVcd* tracep);

void Vregister_file___024root__trace_init_top(Vregister_file___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD static void trace_init(void* voidSelf, VerilatedVcd* tracep, uint32_t code) {
    // Callback from tracep->open()
    Vregister_file___024root* const __restrict vlSelf VL_ATTR_UNUSED = static_cast<Vregister_file___024root*>(voidSelf);
    Vregister_file__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    if (!vlSymsp->_vm_contextp__->calcUnusedSigs()) {
        VL_FATAL_MT(__FILE__, __LINE__, __FILE__,
            "Turning on wave traces requires Verilated::traceEverOn(true) call before time 0.");
    }
    vlSymsp->__Vm_baseCode = code;
    tracep->pushPrefix(std::string{vlSymsp->name()}, VerilatedTracePrefixType::SCOPE_MODULE);
    Vregister_file___024root__trace_decl_types(tracep);
    Vregister_file___024root__trace_init_top(vlSelf, tracep);
    tracep->popPrefix();
}

VL_ATTR_COLD void Vregister_file___024root__trace_register(Vregister_file___024root* vlSelf, VerilatedVcd* tracep);

VL_ATTR_COLD void Vregister_file::traceBaseModel(VerilatedTraceBaseC* tfp, int levels, int options) {
    (void)levels; (void)options;
    VerilatedVcdC* const stfp = dynamic_cast<VerilatedVcdC*>(tfp);
    if (VL_UNLIKELY(!stfp)) {
        vl_fatal(__FILE__, __LINE__, __FILE__,"'Vregister_file::trace()' called on non-VerilatedVcdC object;"
            " use --trace-fst with VerilatedFst object, and --trace with VerilatedVcd object");
    }
    stfp->spTrace()->addModel(this);
    stfp->spTrace()->addInitCb(&trace_init, &(vlSymsp->TOP));
    Vregister_file___024root__trace_register(&(vlSymsp->TOP), stfp->spTrace());
}
