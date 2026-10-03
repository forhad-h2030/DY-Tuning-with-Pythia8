/// Fun4SQHitDst.C: Fun4All macro to extract SQHitVector from DST files.
R__LOAD_LIBRARY(libcalibrator)
R__LOAD_LIBRARY(libktracker)

int reduce(){

	Fun4AllServer* se = Fun4AllServer::instance();
	se->Verbosity(1);
	int n_events = 1000;

	const std::string DST_in = "DST.root";  // Define file name

	 Fun4AllInputManager *in = new Fun4AllDstInputManager("DUMMY");
	     se->registerInputManager(in);
	         in->fileopen(DST_in);



	Fun4AllDstOutputManager *out = new Fun4AllDstOutputManager("DSTOUT", "DST2.root");
	    se->registerOutputManager(out);
	        out->AddNode("SQHitVector");


	//in->fileopen(fn_dst);

	se->run(n_events);

	se->End();

	delete se;

	return 0;
}
