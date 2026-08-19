module register_file (
    input  logic        clk,
    input  logic        we,
    input  logic [4:0]  rs1,
    input  logic [4:0]  rs2,
    input  logic [4:0]  rd,
    input  logic [31:0] wdata,
    output logic [31:0] rdata1,
    output logic [31:0] rdata2
);
    logic [31:0] regs [31:0];

    // Read ports (comb)
    always_comb begin
        rdata1 = (rs1 == 5'b0) ? 32'b0 : regs[rs1];
        rdata2 = (rs2 == 5'b0) ? 32'b0 : regs[rs2];
    end

    // Write port (clocked)
    always_ff @(posedge clk) begin
        if (we && (rd != 5'b0)) begin
            regs[rd] <= wdata;
        end
    end
endmodule
