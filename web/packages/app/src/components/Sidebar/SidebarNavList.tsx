import React from "react";

import { SidebarItemsType } from "../../types/sidebar";
import reduceChildRoutes from "./reduceChildRoutes";

type SidebarNavListProps = {
  depth: number;
  pages: SidebarItemsType[];
};

const SidebarNavList: React.FC<SidebarNavListProps> = (props) => {
  const { pages, depth } = props;

  const currentRoute = "";

  const childRoutes = pages.reduce(
    (items, page) => reduceChildRoutes({ items, page, currentRoute, depth }),
    [] as JSX.Element[]
  );

  return <React.Fragment>{childRoutes}</React.Fragment>;
};

export default SidebarNavList;
