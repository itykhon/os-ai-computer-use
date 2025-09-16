// dart format width=80
// GENERATED CODE - DO NOT MODIFY BY HAND

// **************************************************************************
// InjectableConfigGenerator
// **************************************************************************

// ignore_for_file: type=lint
// coverage:ignore-file

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:frontend_flutter/src/features/chat/application/stores/chat_store.dart'
    as _i513;
import 'package:frontend_flutter/src/features/chat/application/usecases/run_task_usecase.dart'
    as _i912;
import 'package:frontend_flutter/src/features/chat/data/datasources/backend_rest_client.dart'
    as _i286;
import 'package:frontend_flutter/src/features/chat/data/datasources/backend_ws_client.dart'
    as _i468;
import 'package:frontend_flutter/src/features/chat/data/repositories/chat_repository_impl.dart'
    as _i151;
import 'package:frontend_flutter/src/features/chat/domain/repositories/chat_repository.dart'
    as _i673;
import 'package:get_it/get_it.dart' as _i174;
import 'package:injectable/injectable.dart' as _i526;

extension GetItInjectableX on _i174.GetIt {
  // initializes the registration of main-scope dependencies inside of GetIt
  _i174.GetIt init({
    String? environment,
    _i526.EnvironmentFilter? environmentFilter,
  }) {
    final gh = _i526.GetItHelper(this, environment, environmentFilter);
    gh.lazySingleton<_i286.BackendRestClient>(() => _i286.BackendRestClient());
    gh.lazySingleton<_i468.BackendWsClient>(() => _i468.BackendWsClient());
    gh.lazySingleton<_i673.ChatRepository>(
      () => _i151.ChatRepositoryImpl(
        gh<_i468.BackendWsClient>(),
        gh<_i286.BackendRestClient>(),
      ),
    );
    gh.factory<_i513.ChatStore>(
      () => _i513.ChatStore(gh<_i673.ChatRepository>()),
    );
    gh.factory<_i912.RunTaskUseCase>(
      () => _i912.RunTaskUseCase(gh<_i673.ChatRepository>()),
    );
    return this;
  }
}
