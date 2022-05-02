import React from "react";
import styled from "@emotion/styled";
import { CircularProgress } from "@mui/material";

const Root = styled.div`
  justify-content: center;
  align-items: center;
  display: flex;
  min-height: 100%;
`;

function Loader() {
  return (
    <Root>
      <CircularProgress color="secondary" />
    </Root>
  );
}

export default Loader;
