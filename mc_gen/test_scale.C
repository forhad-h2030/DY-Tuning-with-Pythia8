#include "Pythia8/Pythia.h"

void test_scale(const char* cfg = "phpythia8_DY_tune25.cfg", int nevt = 10, const char* pdfHard = "") 
{
  Pythia8::Pythia py("", false);
  py.readFile(cfg);
  py.readString("Beams:idB = 2212");
  py.readString("HadronLevel:all = off");
  py.readString("Next:numberCount = 0");
  if (pdfHard[0] != '\0') py.readString(std::string("PDF:pHardSet = ") + pdfHard);
  if (!py.init()) { printf("PYTHIA init failed (check the cfg path)\n"); return; }

  printf("cfg %s  factorScale2 = %d  factorScale1 = %d  factorMultFac = %.2f\n", cfg,
         py.settings.mode("SigmaProcess:factorScale2"), py.settings.mode("SigmaProcess:factorScale1"),
         py.settings.parm("SigmaProcess:factorMultFac"));
  for (int i = 0; i < nevt; ) { 
    if (!py.next()) continue;
    ++i;
    double Q = sqrt(py.info.Q2Fac());
    printf("mHat %6.3f   Q_fac %6.3f   ratio %.3f\n", py.info.mHat(), Q, Q / py.info.mHat());
  }
}
