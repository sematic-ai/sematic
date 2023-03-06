import { List, ListItem } from "@mui/material";
import { AliasValueViewProps, renderSummary } from "./common";


export default function TupleValueView(props: AliasValueViewProps) {
    let typeRepr = props.typeRepr;
  
    let elementTypesRepr = typeRepr[2].args;
  
    return (
      <List>
        {Array.from(props.valueSummary).map((element, index) => (
          <ListItem key={index}>
            {renderSummary(
              props.typeSerialization,
              element,
              elementTypesRepr[index].type,
              index.toString()
            )}
          </ListItem>
        ))}
      </List>
    );
  }