import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { useTextSelection } from "src/hooks/textSelectionHooks";
import S3 from "src/static/amazon-s3";
import { ValueComponentProps } from "src/typeViz/common";

export function S3LocationValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    const bucketSummary = values.bucket.values;

    return <S3Button region={bucketSummary.region} bucket={bucketSummary.name} location={values.location} />;
}

export function S3BucketValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <S3Button region={values.region} bucket={values.name} />;
}

function S3Button(props: { region?: string, bucket: string, location?: string }) {
    const { region, bucket, location } = props;

    let s3URI = "s3://" + bucket;
    // in case the location points to an object and not to an intermediate
    // "directory", AWS will redirect to the object URL
    let href = new URL("https://s3.console.aws.amazon.com/s3/buckets/" + bucket);
  
    if (region !== null && region !== undefined) {
        href.searchParams.append("region", region);
    }

    if (location !== undefined) {
        s3URI = s3URI + "/" + location;
        href.searchParams.append("prefix", location);
    }

    const elementRef = useTextSelection<HTMLDivElement>();

    return <Tooltip title="View in AWS console">
        <Button
            href={href.href}
            variant="outlined"
            target="blank"
            endIcon={<OpenInNew />}
            draggable={false}
            style={{ userSelect: "text" }}
        >
            <S3 style={{width: "20px", marginRight: "5px"}} />
            <div ref={elementRef} style={{ cursor: "text" }} >{s3URI}</div>
        </Button>
    </Tooltip>;
}
