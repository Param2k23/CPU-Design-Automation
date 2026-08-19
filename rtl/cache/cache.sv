module cache (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        rd_en,
    input  logic        wr_en,
    input  logic [31:0] addr,
    input  logic [31:0] wdata,
    output logic [31:0] rdata,
    output logic        hit,
    output logic        miss
);
    // 4 lines direct mapped cache
    logic [31:0] cache_data [3:0];
    logic [27:0] cache_tag  [3:0];
    logic        cache_valid[3:0];

    logic [1:0]  index;
    logic [27:0] tag;

    assign index = addr[3:2];
    assign tag   = addr[31:4];

    always_comb begin
        if ((rd_en || wr_en) && cache_valid[index] && (cache_tag[index] == tag)) begin
            hit  = 1'b1;
            miss = 1'b0;
            rdata = cache_data[index];
        end else if (rd_en || wr_en) begin
            hit  = 1'b0;
            miss = 1'b1;
            rdata = 32'hdeadbeef; // Default miss data
        end else begin
            hit  = 1'b0;
            miss = 1'b0;
            rdata = 32'b0;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 4; i++) begin
                cache_valid[i] <= 1'b0;
                cache_tag[i]   <= 28'b0;
                cache_data[i]  <= 32'b0;
            end
        end else begin
            if (wr_en) begin
                cache_valid[index] <= 1'b1;
                cache_tag[index]   <= tag;
                cache_data[index]  <= wdata;
            end
        end
    end
endmodule
