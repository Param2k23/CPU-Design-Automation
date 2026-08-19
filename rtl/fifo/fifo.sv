module fifo (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        wr_en,
    input  logic        rd_en,
    input  logic [31:0] din,
    output logic [31:0] dout,
    output logic        full,
    output logic        empty
);
    parameter DEPTH = 8;
    
    logic [31:0] mem [DEPTH-1:0];
    logic [$clog2(DEPTH):0] wr_ptr;
    logic [$clog2(DEPTH):0] rd_ptr;
    logic [$clog2(DEPTH)+1:0] count;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count  <= 0;
            full   <= 0;
            empty  <= 1;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr[$clog2(DEPTH)-1:0]] <= din;
                wr_ptr <= wr_ptr + 1;
            end
            if (rd_en && !empty) begin
                dout <= mem[rd_ptr[$clog2(DEPTH)-1:0]];
                rd_ptr <= rd_ptr + 1;
            end

            // Update status
            case ({wr_en && !full, rd_en && !empty})
                2'b10: count <= count + 1;
                2'b01: count <= count - 1;
                default: ;
            endcase
        end
    end

    always_comb begin
        full  = (count == DEPTH);
        empty = (count == 0);
    end
endmodule
