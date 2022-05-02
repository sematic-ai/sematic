import React from "react";
import { Global, css } from "@emotion/react";

const GlobalStyle = (props: any) => (
  <Global
    {...props}
    styles={css`
      html,
      body,
      #__next {
        height: 100%;
      }

      body {
        margin: 0;
      }

      .MuiCardHeader-action .MuiIconButton-root {
        padding: 4px;
        width: 28px;
        height: 28px;
      }

      body > iframe {
        pointer-events: none;
      }
    `}
  />
);

export default GlobalStyle;