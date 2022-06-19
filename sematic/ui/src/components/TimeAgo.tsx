import jsTimeAgo from "javascript-time-ago";
import en from "javascript-time-ago/locale/en.json";

import ReactTimeAgo from "react-time-ago";

jsTimeAgo.addDefaultLocale(en);

export default function TimeAgo(props: { date: Date }) {
  return <ReactTimeAgo date={new Date(props.date)} locale="en-US" />;
}
