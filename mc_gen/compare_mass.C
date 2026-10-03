#include <ROOT/RDataFrame.hxx>
#include <TCanvas.h>
#include <TH1D.h>
#include <TLegend.h>
#include <TLorentzVector.h>
#include <TStyle.h>
#include <vector>

double MUON_MASS = 0.1056; // GeV/c^2

static double DimuMass(const std::vector<double>& pxp, const std::vector<double>& pyp, const std::vector<double>& pzp,
                       const std::vector<double>& pxn, const std::vector<double>& pyn, const std::vector<double>& pzn)
{
  if (pxp.empty() || pxn.empty()) return -1;
  TLorentzVector p, n;
  p.SetXYZM(pxp[0], pyp[0], pzp[0], MUON_MASS);
  n.SetXYZM(pxn[0], pyn[0], pzn[0], MUON_MASS);
  return (p + n).M();
}

TH1D* MakeHist(const char* file, const char* name)
{
  ROOT::RDataFrame df("tree", file);
  auto h = df.Define("mass", DimuMass,
                     {"rec_dimuon_px_pos_tgt", "rec_dimuon_py_pos_tgt", "rec_dimuon_pz_pos_tgt",
                      "rec_dimuon_px_neg_tgt", "rec_dimuon_py_neg_tgt", "rec_dimuon_pz_neg_tgt"})
             .Filter("mass > 0")
             .Histo1D({name, ";M_{#mu#mu} [GeV/c^{2}];Entries", 60, 0., 12.}, "mass");
  return (TH1D*)h->Clone(name);
}

void compare_mass()
{
  gStyle->SetOptStat(0);
  TH1D* hw  = MakeHist("DY_with_roads_test.root", "h_with");
  TH1D* hwo = MakeHist("DY_without_roads_test.root", "h_without");
  int nw = hw->GetEntries(), nwo = hwo->GetEntries();

  // right pad: unit-area copies
  TH1D* hwn  = (TH1D*)hw->Clone("h_with_norm");
  TH1D* hwon = (TH1D*)hwo->Clone("h_without_norm");
  hwn->Scale(1. / hwn->Integral());
  hwon->Scale(1. / hwon->Integral());
  hwn->GetYaxis()->SetTitle("Normalized entries");

  TCanvas* c = new TCanvas("c", "mass comparison", 1400, 600);
  c->Divide(2, 1);

  TH1D* first[2]  = {hw, hwn};
  TH1D* second[2] = {hwo, hwon};
  for (int i = 0; i < 2; ++i) {
    c->cd(i + 1);
    first[i]->SetLineColor(kRed + 1);   first[i]->SetLineWidth(2);
    second[i]->SetLineColor(kBlue + 1); second[i]->SetLineWidth(2);
    first[i]->SetMaximum(1.3 * std::max(first[i]->GetMaximum(), second[i]->GetMaximum()));
    first[i]->Draw("HIST");
    second[i]->Draw("HIST SAME");
    TLegend* leg = new TLegend(0.50, 0.72, 0.88, 0.88);
    leg->AddEntry(first[i],  Form("With roads (N=%d)", nw), "l");
    leg->AddEntry(second[i], Form("Without roads (N=%d)", nwo), "l");
    leg->Draw();
  }
  c->SaveAs("DY_mass_roads_comparison.png");
}
