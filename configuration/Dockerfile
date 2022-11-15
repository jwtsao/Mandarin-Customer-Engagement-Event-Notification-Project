FROM public.ecr.aws/lambda/python:3.8

# COPY lib/ "${LAMBDA_TASK_ROOT}/lib"
ENV PYTHONPATH "${PYTHONPATH}:${LAMBDA_TASK_ROOT}/lib/python3.8/site-packages/"

ENV LAMBDA_LANG_ROOT="/var/lang"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${LAMBDA_TASK_ROOT}/lib"
ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}:${LAMBDA_TASK_ROOT}/bin:${LAMBDA_TASK_ROOT}/sbin"

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE

RUN echo 'import site; import os; site.addsitedir(os.path.join(os.environ["LAMBDA_TASK_ROOT"], "lib/python3.8/site-packages"))' > ${LAMBDA_LANG_ROOT}/lib/python3.8/site-packages/brazil-site-packages.pth


COPY . ${LAMBDA_TASK_ROOT}
COPY aws_lambda ${LAMBDA_TASK_ROOT}

CMD ["handlers.event_handler"]