import { Components, Theme } from '@mui/material/styles';
import { fontFamilyCode, fontWeightBold } from 'src/theme/new/typography';
import { KeyboardArrowDown } from "@mui/icons-material";
import { selectClasses } from '@mui/material/Select'
import { inputBaseClasses } from '@mui/material/InputBase'

const components: Components = {
    MuiCssBaseline: {
        styleOverrides: ((theme: Theme) => ({
            h2: {
                color: theme.palette.lightGrey.main,
                fontSize: theme.typography.small.fontSize,
                lineHeight: 1,
                textTransform: 'uppercase',
                marginTop: 0,
            },
            pre: {
                whiteSpace: 'pre-wrap'
            }
        })) as any
    },
    MuiLink: {
        defaultProps: {
            underline: 'none'
        },
        styleOverrides: {
            root: (({ theme }: { theme: Theme }) => ({
                cursor: 'pointer',
                marginBottom: 0,
                color: theme.palette.black.main,
                fontSize: theme.typography.fontSize,
                fontStyle: 'italic',

                '&:hover': {
                    color: theme.palette.primary.main,
                }
            })) as any
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
                style: ({ theme }) => {
                    return {
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        color: theme.palette.black.main,
                        width: 'fit-content',
                        fontSize: 14,
                        fontStyle: 'normal',
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
                            bottom: 0,
                            display: 'none',
                        },
                        '&.selected': {
                            position: 'relative'
                        },
                        '&.selected::after': {
                            display: 'block',
                            backgroundColor: theme.palette.primary.main
                        }
                    }
                },
            },
            {
                props: { variant: 'small' },
                style: ({ theme }) => ({
                    color: theme.palette.lightGrey.main,
                    fontSize: theme.typography.small.fontSize,
                }),
            },
            {
                props: { type: 'code' },
                style: {
                    fontFamily: fontFamilyCode,
                },
            }
        ]
    },
    MuiTypography: {
        defaultProps: {
            paragraph: true
        },
        styleOverrides: {
            root: {
                marginBottom: 0,
            }
        },
        variants: [
            {
                props: { variant: 'code' },
                style: ({ theme }) => {
                    return {
                        color: theme.palette.mediumGrey.main,
                    }
                }
            }
        ]
    },
    MuiFormControl: {
        variants: [
            {
                props: { size: 'small' },
                style: {
                    [`& .${inputBaseClasses.root}`]: {
                        height: 25
                    },

                    [`& .${selectClasses.icon}`]: {
                        width: 20,
                        height: 20,
                        right: 3,
                        top: 'calc(50% - 10px)'
                    }
                }
            }
        ]
    },
    MuiTextField: {
        defaultProps: {
            InputProps: {
                disableUnderline: true
            }
        }
    },
    MuiSelect: {
        defaultProps: {
            IconComponent: KeyboardArrowDown
        }
    },
    MuiOutlinedInput: {
        styleOverrides: {
            notchedOutline: (({ theme }: { theme: Theme }) => ({
                border: `1px solid ${theme.palette.p3border.main}`,
            })) as any
        }
    },
    MuiChip: {
        styleOverrides: {
            root: {
                height: 25,
                borderRadius: 0,
            },
            label: (({ theme }: { theme: Theme }) => ({
                fontSize: theme.typography.small.fontSize,
                padding: 5
            })) as any
        }
    },
    MuiButton: {
        variants: [
            {
                props: { variant: 'text' },
                style: ({ theme }) => {
                    return {
                        fontStyle: 'italic',
                        color: theme.palette.lightGrey.main,
                        '&:hover': {
                            color: theme.palette.primary.main,
                            background: 'transparent',
                        }
                    }
                }


            },
            {
                props: { size: 'small' },
                style: ({ theme }) => {
                    return {
                        fontSize: theme.typography.small.fontSize,
                    }
                }
            }
        ]
    },
    MuiListItemButton: {
        styleOverrides: {
            root: (({ theme }: { theme: Theme }) => ({
                '&:hover': {
                    color: theme.palette.primary.main,
                    background: 'transparent',
                },
            })) as any
        }
    },
    MuiTooltip: {
        styleOverrides: {
            tooltipPlacementBottom: (({ theme }: { theme: Theme }) => ({
                'marginTop': `${theme.spacing(1.5)}!important`,
            })) as any
        }
    },
    MuiTab: {
        styleOverrides: {
            "root": (({ theme }: { theme: Theme }) => ({
                "&.Mui-selected": {
                    'color': `${theme.palette.black.main}`
                }
            })) as any
        }
    }

}

export default components;