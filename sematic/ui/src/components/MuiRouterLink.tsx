import Link from "@mui/material/Link";
import { Link as RouterLink } from "react-router-dom";

type LinkPropsType = React.ComponentProps<typeof Link>;
type RouterLinkPropsType = React.ComponentProps<typeof RouterLink>;

type MuiRouterLinkAllProps = LinkPropsType & RouterLinkPropsType;
type OptionalHrefProps = Omit<MuiRouterLinkAllProps, 'href'> 
    & Partial<Pick<LinkPropsType, 'href'>> & Required<Pick<RouterLinkPropsType, 'to'>>
type OptionalToProps = Omit<MuiRouterLinkAllProps, 'to'> 
    & Partial<Pick<RouterLinkPropsType, 'to'>> & Required<Pick<LinkPropsType, 'href'>>

export default function MuiRouterLink(
    props: MuiRouterLinkAllProps | OptionalHrefProps | OptionalToProps) {
    const {href, to, ...restProps} = props;
    let linkDestination = to || href;
    return <Link {...restProps} to={linkDestination!} component={RouterLink} />;
}
