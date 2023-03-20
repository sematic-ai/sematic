import { Components } from '@mui/material/styles';

const components: Components = {
    MuiButton: {
        variants: [
            {
                props: { variant: 'logo' },
                style: {
                    textTransform: 'none',
                    width: 50,
                    height: 50,
                    minWidth: 'min-content'
                },
            },
            {
                props: { variant: 'menu' },
                style: ({theme}) => {
                    return {
                        color: theme.palette.black.main,
                        fontSize: 14,
                        width: 100,
                        padding: 0,
                        height: 50,
                        overflow: 'ellipsis',
                        textTransform: 'none'
                    }
                },
            }
        ]
    }
}

export default components;