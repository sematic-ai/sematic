function createData(
    id: number,
    createdAt: string,
    name: string,
    tags: Array<string>,
    status: string
  ) {
    return { id, createdAt, name, tags, status };
  }
  
  const runData = [
    createData(
      0,
      "16 Mar, 2019",
      "Auto Featurization",
      ["experiment-blahsd", "random-tag"],
      "success"
    ),
    createData(
      1,
      "16 Mar, 2019",
      "Train model",
      ["experiment-blahsd", "randfdsf"],
      "success"
    ),
    createData(
      2,
      "16 Mar, 2019",
      "Train model",
      ["experiment-blahsd", "2daf-tags", "dadceef"],
      "failed"
    ),
    createData(
      3,
      "15 Mar, 2019",
      "Evaluate model",
      ["ddasgfa"],
      "success"
    ),
  ];

  export default runData;
  