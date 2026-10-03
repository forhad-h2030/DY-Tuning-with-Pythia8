#include <ROOT/RDataFrame.hxx>
#include <TCanvas.h>
#include <TH1D.h>
#include <TLorentzVector.h>
#include <TStyle.h>
#include <vector>

double MUON_MASS = 0.1056; // GeV/c^2

// same mass definition as Convert_DY/write.C; -1 if missing
static double DimuMass(const std::vector<double>& pxp, const std::vector<double>& pyp, const std::vector<double>& pzp,
                       const std::vector<double>& pxn, const std::vector<double>& pyn, const std::vector<double>& pzn)
{
  if (pxp.empty() || pxn.empty()) return -1;
  TLorentzVector p, n;
  p.SetXYZM(pxp[0], pyp[0], pzp[0], MUON_MASS);
  n.SetXYZM(pxn[0], pyn[0], pzn[0], MUON_MASS);
  return (p + n).M();
}

void draw_with_roads()
{
  gStyle->SetOptStat(1111); // name, entries, mean, RMS
  ROOT::RDataFrame df("tree", "DY_with_roads_test_pTHat_0.5_legacy_with_weight.root");
  auto h = df.Define("mass", DimuMass,
                     {"rec_dimuon_px_pos_tgt", "rec_dimuon_py_pos_tgt", "rec_dimuon_pz_pos_tgt",
                      "rec_dimuon_px_neg_tgt", "rec_dimuon_py_neg_tgt", "rec_dimuon_pz_neg_tgt"})
             .Filter("mass > 0")
             .Histo1D({"h_with", "DY (Pythia8) with road matching;M_{#mu#mu} [GeV/c^{2}];Weighted entries", 60, 0., 12.}, "mass", "weight");

  TCanvas* c = new TCanvas("c2", "with roads", 800, 600);
  h->SetLineColor(kRed + 1);
  h->SetLineWidth(2);
  h->DrawClone("HIST");
  c->SaveAs("DY_mass_with_roads_weighted.png");
}
