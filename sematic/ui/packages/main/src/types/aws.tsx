import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { CommonValueViewProps } from "./common";
import S3Icon from "./s3.png";

export function S3LocationValueView(props: CommonValueViewProps) {
  const { valueSummary } = props;
  const { values } = valueSummary;

  const bucketSummary = values.bucket.values;

  return <S3Button region={bucketSummary.region} bucket={bucketSummary.name} location={values.location} />;
}
  
export function S3BucketValueView(props: CommonValueViewProps) {
  const { valueSummary } = props;
  const { values } = valueSummary;

  return <S3Button region={values.region} bucket={values.name} />;
}

function S3Button(props: {region?: string, bucket: string, location?: string}) {
  const { region, bucket, location } = props;

  let s3URI = "s3://" + bucket;
  let href = new URL("https://s3.console.aws.amazon.com/s3/object/" + bucket);
  
  if (region !== null && region !== undefined) {
    href.searchParams.append("region", region);
  }

  if (location !== undefined) {
    s3URI = s3URI + "/" + location;
    href.searchParams.append("prefix", location);
  }

  return <>
    <Tooltip title="View in AWS console">
      <Button
        href={href.href}
        variant="outlined"
        target="blank"
        endIcon={<OpenInNew />}
      >
        <img src={S3Icon} width="20px" style={{paddingRight: "5px"}} alt="S3 icon"/>
        {s3URI}
      </Button>
    </Tooltip>
  </>;
}