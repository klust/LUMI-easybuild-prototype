# Design 0.4 of the module system

This prototype focuses on the EasyBuild setup.

Changes compared to design 0.3:

  * We implemented only the stack_partition variant to reduce the amount of work.

  * Added a directory with LUA modules to change the presentation of the module tree.

  * Added a partition/common to be able to install software that is suitable for all
    partitions. That module is hidden however. It is there to be able to install
    software in that partition but it will not show up, e.g., in the output of
    "module spider" as a way to reach software.

    Elements of the implementation:

      * Hidden by a line in .modulerc.lua

      * Made sure it does not show up as a path to reach software in "module spider"
        by ensuring that the prepend_path statements of partition/common are not seen
        if mode() == "spider".

      * Add the common software to the path of the other partition modules.

      * Make sure it does not show up in the labeled view but that its software is
        added to the actual partition.

  * Scripts to generate the external modules configuration file for EasyBuild based
    on a Python script that defines the Cray PE compoments and then some more so that
    it should be possible to extend to other configuration files that need the same
    information.

Changes compared to design 0.2:

  * Design 0.2 is robust but it requires generating the software stack and partition
    modules by preprocessing templates. In design 0.3 we seek to avoid this by using
    the Lmod introspection functions, but this requires a different way of setting
    up the module structure to be compatible with the way Lmod handles a module hierarchy.

    A bonus is that it may be easier to from there extend the hierarchy with additional
    levels the way, e.g., Spack would do it.

  * As we ran into problems with the module ``LUMIpartition/L.lua`` where the Lmod
    ``hierarchyA`` function got confused and provided different results than if the
    module were called ``LUMIpartition/C.lua``, we decided to rework some of the names
    and simply use, e.g., ``partition`` for the module name even if that may cause
    confusion with SLURM partitions.

    *This appears to be a very subtle bug in LMOD, and it is not clear what triggers
    it as we have tried with other combinations of module names also appearing in the
    path and different version names of the modules, but couldn't trigger the bug.*

  * The prototype now also demonstrates the use of the ``extensions`` function in Lmod
    module files to make it easier to find extensions provided by some modules (e.g.,
    Python, R or Perl packages).

  * The prototype now also provides a "SitePackage.lua" file for Lmod to demonstrate
    various customizations that can be made this way. This includes an additional message
    in the ``module avail`` method to point the user to other (Lmod-specific) ways
    of searching for certain software, and providing more human-readable labels to
    the blocks in the output of ``module avail``.

  * We also added the detect_LUMI_partition function to SitePackage.lua to take the
    code to detect on which LUMI partition we are running out of the module files so
    that we can change it more easily to something more robust then the current detection
    which is based on the environment variable LUMI_PARTITION that should be set by
    the system.

  * Added an lmodrc.lua file to assign a state to the software stack: Lont-Term Support
    or development. This is done via a property in the module file, a modulerc file
    to ensure that the default is a LTS stack and an lmodrc.lua file to assign labels
    to each state and print a line of information below the table.

  * Also experimented with a modulerc.lua file for the partitions to show version aliases with
    more meaningful but longer names.

  * Added an admin.list file to demo how a user could be warned of deprecated modules.

  * Moved from LUMI-C etc. to C, G, D or L for the LUMI_PARTITION environment variable.

  * We ensure that ``module reload`` works correctly in both variants, with this special
    property:

      * In the stack-partition version, the reload will cause a switch to the partition
        module for the node on which the module reload is executed.

      * In the partition-stack variant with partition/auto loaded, a ``module reload``
        will reload with the software stacks activated for the partition on which the
        ``module reload`` was executed.

Changes compared to design 0.1:

  * We rely on the Cray LMOD modules for the programming environment
    and don't try to copy those to our own directory structures as
    there is not that much to gain from it given the hierarchical
    structure.

  * We avoid reading environment variables in the partition and stack
    modules and instead produce them via running a template through
    the gpp preprocessor. This
    is simpler than letting each module
    remember its settings.
  * We need to see if we will create PrgEnv-* equivalents in the
    LUMI/yy.mm software stacks using EasyBuild (as in CSCS) or via
    our own script, in which case we would put them elsewhere. In that
    case we could even initialise a LUMI/yy.mm software stack without
    using EasyBuild, which granted is not a good match with the
    "EasyBuild first" strategy.


## Difficulties that we need to deal with or experiment with

  * The CSCS approach is to go for fully separated toolchains, rebuilding everything
    in each toolchain, as they use the Cray compiler wrappers at the moment and they
    don't allow having GCC + another compiler loaded. The alternative is to try build
    a fake GCCcore module which would not use the Cray compiler wrappers to compile
    a number of packages and then make that one a subtoolchain of the regular Cray
    toolchains.

    Advantages
      * We may be able to use more of the common toolchains.
      * Some basic Linux libraries are still less tested with Clang then with GCC so
        we would have less problems compiling those packages.

    Disadvantages
      * Sharing with CSCS become harder
      * No guarantee that this would actually work.

    Questions
      * Should we go for a further level in the hierarchy based on the various
        cpe environments, and quid Spack in this case?


## Running and installing the prototypes

  * LMOD must be installed and correctly initialised before trying out the prototypes.
    ``gpp`` is not needed for this version.

  * ``prototypes/design_0.3`` contains two ``make_*`` scripts to build both variants
    of the prototype (in subdirectories of $HOME/appltest/design_0.3).

  * That directory also contains two ``enable_*`` scripts to initialise the environment
    to test the respective prototype. Source the scripts in the shell or use
    ```bash
    eval $(./enable_stack_partition.sh)
    ```
    in that directory. Then try ``module avail`` and ``module help`` to get started.


## Directory layout for modules and software: Hierarchy with software stack first, partition/architecture second, flat otherwise - Prototype module_stack_partition

Here we mount the same file system with applications and modules
everywhere, but within that file system we have binaries for each
architecture in separate directories

Directory hierarchy

  * Cray modules in their own hierarchy.

  * appl

      * modules: Key here was to follow Lmod guidelines on hierarchical structures
        as much as possible, though in fact we end up with a double hierarchy when
        implementing a hierarchical module naming scheme for applications: a hierarchy
        in the software stack activation, and then the hierarchy in the application
        modules.

          * generic: A directory where we store the generic implementations of some
            of the modules below and link to. This directory should not be in the
            MODULEPATH! Note that in the prototype we actually link to the git
            repository to make editing easier. In the real situation this would be
            copies to avoid accidental changes.

          * SoftwareStack: A module file that enables the default Cray
            environment, and one for each of our LUMI software stacks,
            of the form ``LUMI/version.lua``.

          * SystemPartition/LUMI/yy.mm: The next level in the hierarchy. It contains modules by
            LUMI SoftwareStack to enable the different partitions. Structure:
              * The modules are called ``partition/C.lua`` etc.

                *We could not use LUMIpartition as this lead to problems with the Lmod
                ``hierachyA`` function which produced wrong results for ``LUMIpartition/L.lua``
                but not for ``LUMIpartition/C.lua`` even though both modules had identical
                code.*
              * Modules for the ``LUMI/yy.mm`` software stack are in
                ``LUMIpartition/LUMI/yy.mm``.

          * easybuild/LUMI/yy.mm/partition/part: Directory for the EasyBuild-generated
            modules for the ``LUMI/yy.mm`` software stack for the ``LUMI-part``
            partition (``part`` actually being a single letter, except for the software
            that is common to all partitions, where ``part`` is ``common``)

          * spack/LUMI/yy.mm/partition/part: Similar as the above, but for
            Spack-installed software.

          * manual/LUMI/yy.mm/partition/part: Similar as the above, but for
            manually installed software.

      * SW : This is for the actual binaries, lib directories etc. Names are deliberately
        kept short to avoid problems with too long shebang lines. As shebang lines
        do not undergoe variable expansion, we cannot use the EBROOT variables and
        so on in those lines to save space.

          * LUMI-21.02

              * C

                  * EB

                  * SP

                  * MNL

              * G

              * D

              * L

              * common

      * mgmt: Files that are not stored in our GitHub, but are generated
        on the fly and are only useful to those users who want to
        build upon our software stack or for those who install
        software in our stacks. 

          * ebrepo_files

              * LUMI-21.02

                  * LUMI-C

                  * LUMI-G

                  * LUMI-D

                  * LUMI-L

                  * LUMI-common

      * sources

          * easybuild : Sources directory for EasyBuild, organised the EasyBuild way.

      * SystemRepo: GitHub repository with all managed files

          * easybuild

              * easyconfig

              * config: Configuration of EasyBuild

              * Structure for hooks and easyblocks to be decided.



### Advantages

  * Having the software stack as the highest level in the hierarchy
    makes it easy to also make other software stacks available through
    software stack modules that can then each have their own internal
    organisation, e.g., EESSI should it mature enough during the life of
    LUMI and become suitable for LUMI and should we find a distribution
    mechanism that would integrate with LUMI.

  * \...


### Disadvantages

  * \...


## Module design


### Features of the module system on LUMI

  * The module system is organised in software stacks enabled through loading a
    meta-module. ``CrayEnv`` will enable the native Cray environment for developers
    who prefer to do everything themselves, while the ``LYMI/yy.mm`` modules enable
    the LUMI software stacks, based on the corresponding yy.mm version of the Cray
    programming environment.

  * When it matters, the module system will automatically select the software for
    the partition on which the software stack was loaded (and change to the correct
    partition in Slurm batch scripts on ``module reload``). It is always possible
    to overwrite by loading a partition module after (re)loading the software stack
    meta-module.

  * User-friendly presentation with clear labels is the default, and there is a user-friendly
    way to change the presentation through modules rather than by setting LMOD environment
    variables by hand.

  * Discoverability of software is a key feature. The whole module system is designed
    to make it easy to find installed software through ``module spider`` and ``module
    keyword`` even if that software may not be visible at some point through ``module
    avail``.


### Assumptions

  * The system sets an environment variable LUMI_PARTITION with value
    C, G, D or L depending on the node type (CPU compute, GPU compute,
    data and visualisation, login).
    This is used by the SoftwareStack module to then auto-load the
    module for the current partition when it is loaded.

    This is actually not a hard requirement. The only place where this is currently
    used is in SitePackage.lua where we define a site-specific function that should
    be used in module files to request the partition. That function can be implemented
    differently also so that the environment variable is no longer needed.


### Default behaviour when loading modules

  * A user will always need to load a software stack module first.

      * For those software stack modules that further split up according
        to partition (the LUMI/yy.mm modules), the relevant partition
        module will be loaded automatically when loading the software
        stack. This is based on the partition detected by the
        detect_LUMI_partition function defined in SitePackage.lua.

  *  In this variant of the design, we made the SoftwareStack and LUMIpartition
     modules sticky so that once loaded a user can use ``module purge`` if they
     want to continue working in the same software stack but load other packages.


### Module presentation

  * The LUMI module system supports two ways of presenting the module to the users

     1. The default way users user-friendly labels rather than subdirectories to present
        the modules. Sometimes several subdirectories may map to the same label when
        our feeling is that those modules belong together for the regular user.

     2. But of course the view with subdirectories is also supported for the power
        user.

    The implementation of the labeled view is done in the ``avail_hook`` hook in the
    ``SitePackage.lua`` file and is derived from an example in the Lmod manual.

  * To not confront the user directly with all Lmod environment variables that influence
    the presentation of the modules, we also have a set of modules that can be used
    to change the presentation, including

      * Switching between the labeled and subdirectory view

      * Showing extensions in module avail

      * Turn on and off colour in the presentation of the modules as the colour selection
        can never be good for both white background and black background (though of
        course a power user can change the colour defintions in their terminal emulation
        software to ensure that both bright and dark colours are displayed properly).

    The presentation modules are sticky so that ``module purge`` doesn't change the
    presentation of the modules.


### The common software subdirectories

  * We use a hidden partition module (``partition/common``) which can then be recognized
    by the EasyBuild configuration modules to install software in that partition.

      * Hiding is done via a .modulerc.lua file

      * The path to the common software modules is added in the other partition module
        files, always in such a way that the partition-specific directory comes before
        the equivalent common directory to ensure that partition-specific software
        has a higher priority.

      * Morover, the labeling in SitePackage.lua is such that in the labeled view one
        sees the common and partition-specific software is put together.

  * A hidden partition module did show up into the output of ``module spider`` as a way to
    reach certain other modules. This was the case even when it was hidden by using a name
    starting with a dot rather than a modulerc.lua file. This "feature" is also mentioned
    in [Lmod issue #289](https://github.com/TACC/Lmod/issues/289).

      * Our solution was to modify the module file itself to not include the paths when the
        mode is "spider" so that Lmod cannot see that it is a partition module that makes
        other modules available.


## EasyBuild setup


### Transforming information about the Cray PE to other tools

There are three points where we could use information about versions of specific packages
in releases of the Cray PE:

  * We need to define external modules to EasyBuild.

  * We need to define Cray PE components to Spack

  * A module avail hook to hide those modules that are irrelevant to a particular LUMI/yy.mm
    toolchain could also use that information.

There is currently a set of Python scripts that define the components of the PE and
generate the EasyBuild external modules definition file for a particular release of
the PE.

  * ``make_CPE_defs.py`` defines the PE component version numbers and calls the script
    that generates the EasyBuild external modules file.

    If HPE-Cray would deliver the information on the PE components in a different way,
    e.g., a YAML file, it would make sense to rewrite that part.

  * ``lumitools/CPE_to_EB.py`` then generates the EasyBuild external modules file.


### EasyBuild Module Naming Scheme

  * Options

      * A flat naming scheme, even without the module classes as they are of little
        use. May packages belong to more than one class, it is impossible to come up
        with a consistent categorization. Fully omitting the categorization requires
        a slightly customized naming scheme that can be copied from UAntwerpen. When
        combining with --suffix-modules-path='' one can also drop the 'all' subdirectory
        level which is completely unnecessary in that case.

      * A hierarchical naming scheme as used at CSCS and CSC. Note that CSCS has an
        open bug report at the time of writing (May 12) on the standard implementation
        in EasyBuild ([Issue #3626](https://github.com/easybuilders/easybuild-framework/issues/3626)
        and the related [issue 3575](https://github.com/easybuilders/easybuild-framework/issues/3575)).
        The solution might be to develop our own naming scheme module.

  * Current implementation in the prototype:

      * A flat naming scheme that is a slight customization of the default EasyBuildMNS
        without the categories, combined with an empty ``suffix-modules-path`` to avoid
        adding the unnecessary ``all`` subdirectory level in the module tree.

      * As we need to point to our own module naming scheme implementation which is
        hard to do in a configuration file (as the path needs to be hardcoded), the
        settings for the module scheme are done via ``EASYBUILD_*`` environment variables,
        specifically:
          * ``EASYBUILD_INCLUDE_MODULE_NAMING_SCHEMES`` to add out own module naming schemes
          * ``EASYBUILD_MODULE_NAMING_SCHEME=LUMI_FlatMNS``
          * ``EASYBUILD_SUFFIX_MODULES_PATH=''``


### Other configuration decisions

  * TODO: rpath or not?

  * TODO: Hiding many basic libraries


### Running EasyBuild

EasyBuild for LUMI is configured through a set of EasyBuild configuration files and
environment variables. The basic idea is to never load the EasyBuild module directly
without using one of the EasyBuild configuration modules. There are two such modules

  * EasyBuild-production to do the installations in the production directories.

    TODO: By setting an environment variable before loading the module, it is possible
    to do a test build instead. BUT THIS WILL REQUIRE COMPATIBLE CHANGES TO THE MODULES
    THAT LOAD THE SOFTWARE STACKS!

  * EasyBuild-user is meant to do software installations in the home directory of a
    user or in their project directory. This module will configure EasyBuild such that
    it builds on top of the software already installed on the system, with a compatible
    directory structure.

    This module is not only useful to regular users, but also to LUST to develop EasyConfig
    files for installation on the system. We aim to develop the module in such a way
    that being able to install the module in a home or project subdirectory would also
    practically guarantee that the installation will also work in the system directories.


#### The EasyBuild-production module

Most of the settings for EasyBuild on LUMI are controlled through environment variables
as this gives us more flexibility and a setup that we can easily redo in a different
directory (e.g., to test on the test system). Some settings that are independent of
the directory structure and independent of the software stack are still done in regular
configuration files.

There are two regular configuration files:

 1. ``production.cfg`` is always read.

 2. ``production-LUMI-yy.mm.cfg`` is read after ``production.cfg``, hence can be used
    to overwrite settings made in ``production.cfg`` for a specific toolchain. This
    allows us to evolve the configuration files while keeping the possibility to install
    in older versions of the LUMI software stack.

Settings made in the configuration files:

  * Modules tool and modules syntax.

  * Modules that may be loaded when EasyBuild runs

  * Modules that should be hidden. Starting point is currently the list of CSCS. TODO

  * Ignore EBROOT variables without matching module as we use this to implement Bundles
    that are detected by certain EasyBlocks as if each package included in the Bundle
    was installed as a separate package.

The following settings are made through environment variables:

  * The buildpath and path for temporary files. The current implementation creates
    subdirectories in the directory pointed to by ``XDG_RUNTIME_DIR`` as this is a
    RAM-based file system and gets cleaned when the user logs out. This value is based
    on the CSCS setup.

  * Software and module install paths, according to the directory scheme given in the
    module system section.

  * The directory where sources will be stored, as indicated in the directory structure
    overview.

  * The repo directories where EasyBuild stores EasyConfig files for the modules that
    are build, as indicated in the directory structure overview.

  * Easybuild robot paths: we use EASYBUILD_ROBOT_PATHS and not EASYBUILD_ROBOT so
    searching the robot path is not enabled by default but can be controlled through
    the ``-r`` flag of the ``eb`` command. The search order is:

     1. The repository for the currently active partition

     2. The repository for the common partition

     3. The LUMI-specific EasyConfig directory.

    We deliberately put the ebrepo_files repositories first as this ensure that EasyBuild
    will always find the EasyConfig file for the installed module first as changes
    may have been made to the EasyConfig in the LUMI EasyConfig repository that are
    not yet reflected in the installed software.

    The default EasyConfig files that come with EasyBuild are not put in the robot
    search path for two reasons:

     1. They are not made for the Cray toolchains anyway (though one could of course
        use ``--try-toolchain`` etc.)

     2. We want to ensure that our EasyConfig repository is complete so that we can
        impose our own standards on, e.g., adding information to the help block or
        whatis lines in modules, and do not accidentally install dependencies without
        realising this.

  * Names and locations of the EasyBuild configuration files and of the external modules
    definition file.

  * Settings for the module naming scheme: As we need to point to a custom implementation
    of the module naming schemes, this is done through an environment variable. For
    consistency we also set the module naming scheme itself via a variable and set
    EASYBUILD_SUFFIX_MODULES_PATH as that together with the module naming scheme determines
    the location of the modules with respect to the module install path.

  * Custom EasyBlocks

  * Search path for EasyConfig files

     1. Our own EasyConfig repository

     2. Not yet done, but we could maintain a local copy of the CSCS repository and
        enable search in that also.

     3. Default EasyConfig files that come with EasyBuild

     4. Deliberately not included: Our ebrepo_files repositories. Everything in there
        sould be in our own EasyConfig repository if the installations are managed
        properly.

  * ``EASYBUILD_OPTARCH``, TODO: More information needed on how to set this on Cray.

  * Should we ever have custom toolchains then this will also be the place to indicate
    where they can be found.

  * We also set containerpath and packagepath even though we don't plan to use those,
    but it ensures that files produced by this option will not end up in our GitHub
    repository.


#### The EasyBuild-user module

We currently opted for a module that also contains all relevant code of EasyBuild-production
rather than a setup that first loads that module to then overwrite certain variables.

  * The root of the EasyBuild directory structure is pointed to by the
    environment variable ``EBU_USER_PREFIX``. The default value if the variable
    is not defined is ``$HOME/EasyBuild``.

  * The directory structure in that directory largely reflects the system
    directory structure. This may be a bit more complicated than really needed
    for the user who does an occasional install, but is great for user communities
    who install a more ellaborate software stack in their project directory.

    Changes:

       * ``SystemRepo`` is named ``UserRepo`` instead but we do keep it
         as a separate level so that the user can also easily do version
         tracking via a versioning system such as GitHub.

       * The 'mgmt' level is missing as we do not take into account
         subdirectories that might be related to other software management
         tools.

       * As there are only modules generated by EasyBuild in this module tree,
         ``modules/easybuild`` simply becomes ``modules``.




## Starting a new software stack and bootstrapping EasyBuild

  * Create a ``LUMI/yy.mm`` module for the software stack (through linking to
    the generic implementation) and create the necessary partition modules at
    the next level in the software stack hierarchy (again using symbolic links
    to the generic implemenation). Do not forget to adapt (for the LUMI-module)
    or install (for the partition modules) the necessary .modulerc.lua files.

      * The one in the directory with the ``LUMI/yy.mm``-modules is used to
        set the default module so you may want to wait to adapt the default.

      * The one in the partition module directory sets a number of aliases to
        provide more user-readable names for the partitions and hides the common
        partition module.

  * Create the definition file for the external modules for EasyBuild

      * Procedure should be worked out further depending on the information we get
        from Cray. Currently it is a set of Python scripts that define the versions
        of the PE components and generate the file.

  * Add an EasyConfig file for the desired version of EasyBuild to the LUMI EasyConfig
    repository.

  * Check if a software stack-specific configuration file for EasyBuild is needed.

  * Install the EasyBuild-production and EasyBuild-user modules that take care of the
    setup of EasyBuild. This can be done by symlinking to the generic implemenation in
    each of the partitions, including the ``common`` one. Note that the version should
    be the name of the partition.

  * Load the new LUMI module and then ``partition/common``and then ``EasyBuild-production``.
    The latter will produce a warning that no EasyBuild module is found yet, but it
    will produce the correct setup for EasyBuild.

  * Installing EasyBuild using EasyBuild: there are two options:

      * Ensure PYTHONPATH refers to the EasyBuild Python files from another software
        stack and call the corresponding binary using the full path to the ``eb`` script.

      * Install a version of EasyBuild by hand in a temporary directory (it is enough
        to only install the framework and EasyBlocks), point PYTHONPATH to the Python
        files and call the ``eb`` script using the full path. This temporary installation
        can be removed again once EasyBuild is installed.

        This is the procedure that we used in the script that generates the prototype
        (though defining the environment variables in the script rather than through
        a bootstrap module).

  * Create the Cray PE toolchain modules

    TODO: Use a script that uses the same data as used for the external module definition.

  * And now one should be ready to install other software...

      * Ensure the software stack module is loaded and the partition module for the
        location where you want to install the software is loaded (so the hidden module
        partition/common to install software in the location common to all regular
        partitions)

      * Load EasyBuild-production for an install in the production directories or
        EasyBuild-user for an install in the user or project directories (and you'll
        need to set some environment variables beforehand to point to that location).


## Impact of changes

  * Software directory  root (appl/software) and structure

      * ``EasyBuild-production`` module and if we want to reflect the changes in the structure
        of the user directory, also ``EasyBuild-user``.

      * All module files are affected as various variables contain the path to binaries,
        libraries, etc.

      * Some libraries generated by libtool may be affected as the path to dependend libraries
        is sometimes encoded in ``.la`` files.

      * When rpath linking is used, the binaries themselves are also affected.

  * Module directory

      * Changes to the root of the module directory

          * All software stack modules may need changes

          * ``EasyBuild-production`` module and if we want to reflect the changes in the structure
            of the user directory, also ``EasyBuild-user``.

          * ``cpe*`` modules as they expand the module search path in the hierarchy.

      * Changes to the structure of the LUMI toolchain part

          * LUMI software stack modules need changes

          * ``EasyBuild-production`` and ``EasyBuild-user``, not only because it influences
            the directory where modules will be installed but also because the module
            gets its information about the active software stack and partition from
            the directory structure.

            One could consider moving that dependency to ``SitePAckage.lua`` by defining
            a function that returns the active software stack and partition.

          * ``cpe*`` modules as they expand the module search path in the hierarchy.

          * Generation of the labels in ``SitePackage.lua`` may be affected

  * Module naming scheme

      *  ``EasyBuild-production`` and ``EasyBuild-user``, where the module naming schemes
         are set.

      * ``cpe*`` modules as they behave differently in a flat and a hierarchical module
        naming scheme.

      * The whole module tree should be regenerated in case of a change of the module
        naming scheme.

      * It may have impact on the label generation in ``SitePAckage.lua``.