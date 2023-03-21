import { Components } from '@mui/material/styles';
import { fontWeightBold } from 'src/theme/new/typography';

const components: Components = {
    MuiLink: {
        defaultProps: {
            underline: 'none'
        },
        styleOverrides: {
            root: {
                cursor: 'pointer'
            }
        },
        variants: [
            {
                props: { variant: 'logo' },
                style: {
                    display: 'flex',
                    justifyContent: 'center',
                    textTransform: 'none',
                    width: 50,
                    height: 50
                },
            },
            {
                props: { variant: 'subtitle1', type: 'menu' },
                style: ({theme}) => {
                    return {
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        color: theme.palette.black.main,
                        width: 'fit-content',
                        fontSize: 14,
                        marginLeft: 20,
                        marginRight: 20,
                        fontWeight: fontWeightBold,
                        height: 50,
                        overflow: 'ellipsis',
                        '&:hover': {
                            color: theme.palette.primary.main
                        },
                        '&::before': {
                            width: 100,
                            content: '""',
                            height: 0,
                            position: 'relative',
                            marginLeft: -20,
                            marginRight: -20,
                        },
                        '&::after': {
                            width: '100%',
                            paddingLeft: 20,
                            paddingRight: 20,
                            content: '""',
                            height: 2,
                            position: 'absolute',
                            bottom: 0
                        },
                        '&.selected': {
                            position: 'relative'
                        },
                        '&.selected::after': {                            
                            backgroundColor: theme.palette.primary.main                            
                        }
                    }
                },
            }
        ]
    }
}

export default components;