import { Alert, Typography } from "@mui/material";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import { AnyTypeSerialization, renderSummary, TypeParamRepr, ValueViewProps } from "./common";

export type DataclassTypeRepr = [
  "dataclass",
  string,
  { import_path: string; fields: { [name: string]: TypeParamRepr } }
];

export type DataclassValueViewProps = ValueViewProps<DataclassTypeRepr>;

export default function DataclassValueView(props: ValueViewProps<DataclassTypeRepr>) {
  let valueSummary: {
    values: { [name: string]: any };
    types: { [name: string]: AnyTypeSerialization };
  } = props.valueSummary;

  let typeRepr = props.typeRepr;
  let typeFields = typeRepr[2].fields;
  if (typeFields === undefined) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  return (
    <Stack>
      {Object.entries(valueSummary.values).map<React.ReactNode>(
        ([name, fieldSummary]) => (
          <Box
            key={name}
            sx={{ borderBottom: 1, borderColor: "#f0f0f0", py: 5 }}
          >
            <Typography variant="h6">{name}</Typography>
            <Box sx={{ mt: 3, pl: 5 }}>
              {renderSummary(
                valueSummary.types[name] || props.typeSerialization,
                fieldSummary,
                valueSummary.types[name]?.type || typeFields[name].type
              )}
            </Box>
          </Box>
        )
      )}
    </Stack>
  );
}