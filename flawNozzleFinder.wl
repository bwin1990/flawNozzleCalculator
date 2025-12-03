Clear["Global`*"];
file = SystemDialogInput["FileOpen"]
If[file =!= $Canceled, 
 data = Import[file, "Dataset", HeaderLines -> 1]]
(*分开数据中属于A,T,C,G,ACT的数据，用于单独计算，空数据报Failure也没关系*)
{Adata, Tdata, Cdata, Gdata, ACTdata, A1data, T1data, C1data, G1data, 
  ACT1data} = 
 GroupBy[DeleteDuplicates[data[All, {"Label", "X", "Y"}]], 
     "Label"][#] & /@ {"A.tif", "T.tif", "C.tif", "G.tif", "ACT.tif", 
   "A1.tif", "T1.tif", "C1.tif", "G1.tif", "ACT1.tif"}

(*有时后墨滴为斜线，需要旋转成竖直*)
rotateToVertical[ds_] := 
  Module[{sortds, vec, angle, rotationMatrix, newds},
   sortds = ds[SortBy[#X &]];
   vec = Values@Normal@sortds[-1, {"X", "Y"}] - 
     Values@Normal@sortds[1, {"X", "Y"}];
   angle = ArcTan[First[vec], Last[vec]];
   rotationMatrix = {{Cos[-angle], -Sin[-angle]}, {Sin[-angle], 
      Cos[-angle]}};
   newds = 
    Dataset[rotationMatrix.# & /@ Values[Normal[ds[All, {"X", "Y"}]]]];
   newds = newds[All, <|"X" -> 1, "Y" -> 2|>]
   ];
findNozzle[lis_, sn_] := 
 Module[{sortlist, step, mid, start, end, appro}, 
  sortlist = Sort[lis]; start = First@sortlist; end = Last@sortlist; 
  mid = Most[Rest[sortlist]]; step = (end - start)/(sn - 1);
  
  appro[x_] := 
   If[Abs[Round[((x - start)/step + 1)] - ((x - start)/step + 1)] < 
     0.25, Round[((x - start)/step + 1)], "out of range"];
  Map[appro, mid]
  ](*导入list，以mid为墨滴坐标，计算index数目*)
autoCalFlaw[ds_] :=
  If[Head[ds] === Failure, {},(*剔除failure防报错*)
   Normal[findNozzle[rotateToVertical[ds][All, "X"], 636]]
   ];
totalFlawList = 
 Sort[DeleteDuplicates[
   Flatten[Map[
     autoCalFlaw, {Adata, Tdata, Cdata, Gdata, ACTdata, A1data, 
      T1data, C1data, G1data, ACT1data}]]]]  

Export["flaw_nozzle_" <> DateString[{"Year", "Month", "Day"}] <> 
  "_680k" <> "_04" <> ".txt", totalFlawList]