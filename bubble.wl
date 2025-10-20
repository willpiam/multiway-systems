n = 3;
inits = Permutations[Range[n]];

bubbleNeighbors[list_List] := Module[{res = {}, k = Length[list]},
  Do[
    If[list[[i]] > list[[i + 1]]],
      AppendTo[res, ReplacePart[list, {i -> list[[i + 1]], i + 1 -> list[[i]]}]]
    ],
    {i, 1, k - 1}
  ];
  res
];

edges = Flatten[Table[Thread[p -> bubbleNeighbors[p]], {p, inits}], 1];

g = Graph[inits, edges,
  VertexLabels -> "Name",
  GraphLayout -> "LayeredDigraphEmbedding",
  DirectedEdges -> True
];

Export["multiway-bubble.png", g, "PNG"]
