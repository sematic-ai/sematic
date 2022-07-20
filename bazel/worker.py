from sematic.resolvers.worker import main, parse_args

if __name__ == "__main__":
    main(**vars(parse_args()))
