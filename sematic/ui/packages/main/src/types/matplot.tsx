import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { CommonValueViewProps } from "./common";
import { useMatplotLib } from "../hooks/useMatplotLib";
import { v4 as uuidv4 } from "uuid";
import useMeasure from "react-use/lib/useMeasure";
import "react-medium-image-zoom/dist/styles.css";
import ImageValueView from "src/types/image";

interface MatplotlibFigureValueFigureProps {
  spec: any;
}

function MatplotlibFigureValueFigure(props: MatplotlibFigureValueFigureProps) {
  const { spec: specProp } = props;
  const figureId = useMemo(() => `fig-${uuidv4()}`, []);

  const drawFigure = useMatplotLib(figureId);

  const [figDivRef, { width, height }] = useMeasure<HTMLDivElement>();

  const hasFigureRendered = useRef(false);

  const [scaleAndTranslate, setScaleAndTranslate] = useState({
    scale: 1,
    translate: { x: 0, y: 0 },
  });

  const [scaledHeight, setScaleHeight] = useState(0);

  useLayoutEffect(() => {
    // wait for the element's final layout when its width is fully expanded.
    if (!hasFigureRendered.current && width > 0) {
      const spec = {
        ...specProp,
        plugins: [],
      };

      const scaledHeight = (width / spec.width) * spec.height;

      drawFigure(spec);

      const scale = width / spec.width;

      setScaleHeight(scaledHeight);
      setScaleAndTranslate({
        scale: scale,
        translate: {
          x: (width - spec.width) / 2,
          y: (scaledHeight - spec.height) / 2,
        },
      });

      hasFigureRendered.current = true;
    }
  }, [width, height, drawFigure, figureId, specProp]);

  return (
    <div ref={figDivRef} style={{ width: "100%", height: `${scaledHeight}px` }}>
      <div
        id={figureId}
        style={{
          width: "100%",
          height: "100%",
          transform:
            `scale(${scaleAndTranslate.scale})` +
            ` translate(${scaleAndTranslate.translate.x}px, ${scaleAndTranslate.translate.y}px)`,
        }}
      />
    </div>
  );
}

// This component can be entirely removed and replaced with ImageValueView
// a couple of releases after 0.28.0
// TODO: https://github.com/sematic-ai/sematic/issues/700
export default function MatplotlibFigureValueView(props: CommonValueViewProps) {
  let { valueSummary } = props;

  const hasFigureJsonData = useMemo(
    () => !!valueSummary["mpld3"],
    [valueSummary]
  );

  return hasFigureJsonData ? (
    <MatplotlibFigureValueFigure
      key={valueSummary["mpld3"]["id"]}
      spec={valueSummary["mpld3"]}
    />
  ) : (
    <ImageValueView valueSummary={valueSummary} />
  );
}
