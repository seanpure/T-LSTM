import torch.nn as nn
import torch
import torch.nn.functional as F

from Layers import ReSentenceMatrixLayer, SentenceMatrixLayer, GCN
from Model.G2E.attention import MultiHeadedAttention
from Model.G2E.gcn.GraphConvolution import GraphConvolution
from .Layer import Decoder, Encoder, InputLayers, PreLayers


class H_lstm(nn.Module):
    def __init__(self,vocab_len, in_size=300,lstm_h_size=1200, g_out_size=300,at_size=1200,l_h_size=300, out_size=1,
                 dropout=0.3, bi=True,Ec_layer=2):
        super(H_lstm, self).__init__()
        self.ELayer_nums = Ec_layer
        self.embedding = nn.Embedding(vocab_len, in_size)
        self.dropout=nn.Dropout(dropout)
        self.lstm=nn.LSTM(in_size,in_size,num_layers=2,batch_first=True,dropout=dropout,bidirectional=True)
        self.gcn=GCN(in_size,in_size*2,in_size*2,dropout)
        self.dropout = nn.Dropout(dropout)
        # self.Decoder = MultiHeadedAttention(1,lstm_h_size, lstm_h_size)
        self.PreLayer = PreLayers(in_size*4, l_h_size, out_size)

    def forward(self, x, adj, trigger, mask=None):
        x = self.embedding(x)
        lstm_x,_ = self.lstm(x)
        gcn_x = self.gcn(x,adj)
        x = torch.cat((lstm_x,gcn_x),-1)
        one_hot = F.one_hot(torch.arange(0, trigger.max() + 1), x.shape[1]).to(trigger.device)
        trigger = one_hot[trigger].unsqueeze(-1)
        trigger = trigger.expand(trigger.shape[0], trigger.shape[1], x.shape[-1]).bool()
        # print("----------trigger----------------")
        # print(trigger)
        trigger_x = x.masked_select(trigger).reshape(x.shape[0], 1, x.shape[-1])
        # print("----------trigger_x----------------")
        # print(trigger_x.shape)
        x = self.PreLayer(trigger_x)
        return x.squeeze()


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = GraphState2eep(10).to(device)
    x = torch.rand(4, 5, 10).to(device)
    adj = torch.ones(4, 5, 5).to(device)
    trigger = torch.tensor([1, 2, 3, 4]).to(device)
    mask = torch.ones(4, 5).to(device)
    out = model(x, trigger, adj, mask)
    print(out.shape)
