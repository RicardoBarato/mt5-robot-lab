//+------------------------------------------------------------------+
//| MT5 Robot Lab - SmokeHarness_Public                              |
//| Public, non-trading Strategy Tester smoke harness.                |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"
#property description "Public smoke harness for MT5 Robot Lab. It performs no position actions."

input string SmokeLabel = "MT5 Robot Lab public smoke harness";

int OnInit()
  {
   Print("MT5 Robot Lab smoke init: ", SmokeLabel);
   return(INIT_SUCCEEDED);
  }

void OnTick()
  {
   // Intentionally empty: this harness only proves tester load/execution.
  }

void OnDeinit(const int reason)
  {
   Print("MT5 Robot Lab smoke deinit: ", reason);
  }

double OnTester()
  {
   return(0.0);
  }
